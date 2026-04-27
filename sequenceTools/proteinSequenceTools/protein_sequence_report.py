#!/usr/bin/env python3
"""Utilities for protein sequence tools.

The functions in this module are intentionally dataset-agnostic. They parse FASTA
records, compute sequence descriptors, query RCSB by sequence, fetch polymer
entity metadata, and align query sequences to candidate structures.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from Bio import SeqIO
from Bio.Align import PairwiseAligner
from Bio.Align import substitution_matrices
from Bio.SeqUtils.ProtParam import ProteinAnalysis

CANONICAL_AA = set("ACDEFGHIKLMNPQRSTVWY")

DATA_SOURCES = [
    {
        "name": "Biopython",
        "kind": "local library",
        "url": "https://biopython.org/",
        "use": "FASTA parsing, protein sequence descriptors and pairwise alignment with BLOSUM62",
    },
    {
        "name": "RCSB PDB Search API",
        "kind": "public API",
        "url": "https://search.rcsb.org/rcsbsearch/v2/query",
        "use": "protein sequence search against experimental PDB polymer entities",
    },
    {
        "name": "RCSB PDB Data API",
        "kind": "public API",
        "url": "https://data.rcsb.org/rest/v1/core/",
        "use": "PDB entry, polymer entity, chain, ligand, SIFTS and annotation metadata",
    },
    {
        "name": "UniProt REST API",
        "kind": "public API",
        "url": "https://rest.uniprot.org/uniprotkb/",
        "use": "gene names, protein names, EC numbers, functional comments, PTMs and residue features",
    },
    {
        "name": "AlphaFold DB API",
        "kind": "public API",
        "url": "https://alphafold.ebi.ac.uk/api/prediction/",
        "use": "AlphaFold DB model links for UniProt accessions",
    },
    {
        "name": "BRENDA",
        "kind": "external database link",
        "url": "https://www.brenda-enzymes.org/",
        "use": "manual EC-number follow-up when UniProt/PDB metadata provide EC numbers",
    },
]

TAG_PATTERNS = {
    "polyhistidine": re.compile(r"H{6,}"),
    "flag": re.compile(r"DYKDDDDK?|MDYKDDDDK?"),
    "strep_ii": re.compile(r"WSHPQFEK"),
    "tev_site": re.compile(r"ENLYFQG"),
}


@dataclass
class AlignmentStats:
    query_start: int | None
    query_end: int | None
    target_start: int | None
    target_end: int | None
    query_coverage: float
    target_coverage: float
    identity: float
    matches: int
    aligned_pairs: int
    score: float


@dataclass
class PdbHit:
    pdb_id: str
    entity_id: str
    search_score: float | None
    title: str | None
    description: str | None
    method: str | None
    resolution: float | None
    chains: list[str]
    sequence_length: int
    uniprot_refs: list[str]
    sifts_refs: list[dict[str, Any]]
    alignment: AlignmentStats
    flags: list[str]


def parse_fasta(path: str | Path, id_source: str = "auto") -> list[dict[str, str]]:
    raw_records = list(SeqIO.parse(str(path), "fasta"))
    if not raw_records:
        raise ValueError(f"No FASTA records found in {path}")
    if id_source == "auto":
        ids = choose_auto_identifiers(raw_records)
    else:
        ids = [record_identifier(rec, id_source, i + 1) for i, rec in enumerate(raw_records)]
    records = []
    seen: dict[str, int] = {}
    for index, (rec, seq_id) in enumerate(zip(raw_records, ids), 1):
        seq = normalize_sequence(str(rec.seq))
        if not seq_id:
            seq_id = f"sequence_{index}"
        seen[seq_id] = seen.get(seq_id, 0) + 1
        if seen[seq_id] > 1:
            seq_id = f"{seq_id}_{seen[seq_id]}"
        records.append({"id": seq_id, "description": rec.description, "sequence": seq})
    return records


def choose_auto_identifiers(records: list[Any]) -> list[str]:
    candidates = [
        [record_identifier(rec, "record_id", i + 1) for i, rec in enumerate(records)],
        [record_identifier(rec, "last_token", i + 1) for i, rec in enumerate(records)],
        [record_identifier(rec, "first_token", i + 1) for i, rec in enumerate(records)],
    ]
    for ids in candidates:
        if useful_identifier_set(ids):
            return ids
    return [f"sequence_{i + 1}" for i in range(len(records))]


def useful_identifier_set(ids: list[str]) -> bool:
    if len(set(ids)) != len(ids):
        return False
    for seq_id in ids:
        if not seq_id or len(seq_id) > 40:
            return False
        if len(seq_id) <= 2 and seq_id.lower() in {"jc", "id", "seq"}:
            return False
    return True


def record_identifier(rec: Any, id_source: str, index: int = 1) -> str:
    tokens = rec.description.split()
    if id_source == "record_id":
        return rec.id
    if id_source == "description":
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", rec.description).strip("_")
    if id_source == "first_token":
        return tokens[0] if tokens else rec.id
    if id_source == "last_token":
        return tokens[-1] if tokens else rec.id
    if id_source == "index":
        return f"sequence_{index}"
    raise ValueError(f"Unknown id_source: {id_source}")

def normalize_sequence(seq: str) -> str:
    return re.sub(r"[^A-Za-z*]", "", seq).replace("*", "").upper()


def sequence_features(seq: str) -> dict[str, Any]:
    canonical = "".join(aa for aa in seq if aa in CANONICAL_AA)
    unknown_positions = [i + 1 for i, aa in enumerate(seq) if aa not in CANONICAL_AA]
    analysis = ProteinAnalysis(canonical) if canonical else None
    counts = {aa: seq.count(aa) for aa in sorted(CANONICAL_AA)}
    tags = []
    for name, pattern in TAG_PATTERNS.items():
        for match in pattern.finditer(seq):
            tags.append({"type": name, "start": match.start() + 1, "end": match.end(), "sequence": match.group(0)})
    cysteines = [i + 1 for i, aa in enumerate(seq) if aa == "C"]
    n_glyco = [m.start() + 1 for m in re.finditer(r"N[^P][ST][^P]", seq)]
    result: dict[str, Any] = {
        "length": len(seq),
        "canonical_length": len(canonical),
        "unknown_count": len(unknown_positions),
        "unknown_positions": unknown_positions,
        "aa_counts": counts,
        "cysteine_count": len(cysteines),
        "cysteine_positions": cysteines,
        "n_glycosylation_motif_positions": n_glyco,
        "tags": tags,
        "acidic_fraction": fraction(seq, set("DE")),
        "basic_fraction": fraction(seq, set("KRH")),
        "hydrophobic_fraction": fraction(seq, set("AILMFWYV")),
    }
    if analysis:
        result.update({
            "molecular_weight_da": analysis.molecular_weight(),
            "isoelectric_point": analysis.isoelectric_point(),
            "aromaticity": analysis.aromaticity(),
            "instability_index": analysis.instability_index(),
            "gravy": analysis.gravy(),
        })
        try:
            helix, turn, sheet = analysis.secondary_structure_fraction()
            result.update({"helix_fraction_estimate": helix, "turn_fraction_estimate": turn, "sheet_fraction_estimate": sheet})
        except Exception:
            pass
    return result


def fraction(seq: str, chars: set[str]) -> float:
    return sum(1 for aa in seq if aa in chars) / len(seq) if seq else 0.0


def build_aligner() -> PairwiseAligner:
    aligner = PairwiseAligner()
    aligner.mode = "local"
    aligner.substitution_matrix = substitution_matrices.load("BLOSUM62")
    aligner.open_gap_score = -10
    aligner.extend_gap_score = -0.5
    return aligner


def align_sequences(query: str, target: str) -> AlignmentStats:
    if not query or not target:
        return AlignmentStats(None, None, None, None, 0.0, 0.0, 0.0, 0, 0, 0.0)
    aligner = build_aligner()
    aln = aligner.align(query, target)[0]
    q_blocks = aln.aligned[0]
    t_blocks = aln.aligned[1]
    if len(q_blocks) == 0:
        return AlignmentStats(None, None, None, None, 0.0, 0.0, 0.0, 0, 0, float(aln.score))
    matches = 0
    aligned_pairs = 0
    q_aligned = 0
    t_aligned = 0
    for (qs, qe), (ts, te) in zip(q_blocks, t_blocks):
        q_aligned += qe - qs
        t_aligned += te - ts
        for q_i, t_i in zip(range(qs, qe), range(ts, te)):
            aligned_pairs += 1
            if query[q_i] == target[t_i]:
                matches += 1
    return AlignmentStats(
        query_start=int(q_blocks[0][0]) + 1,
        query_end=int(q_blocks[-1][1]),
        target_start=int(t_blocks[0][0]) + 1,
        target_end=int(t_blocks[-1][1]),
        query_coverage=q_aligned / len(query),
        target_coverage=t_aligned / len(target),
        identity=matches / aligned_pairs if aligned_pairs else 0.0,
        matches=matches,
        aligned_pairs=aligned_pairs,
        score=float(aln.score),
    )


def rcsb_sequence_search(seq: str, top: int = 10, identity_cutoff: float = 0.25, evalue_cutoff: float = 10.0) -> list[dict[str, Any]]:
    payload = {
        "query": {
            "type": "terminal",
            "service": "sequence",
            "parameters": {
                "evalue_cutoff": evalue_cutoff,
                "identity_cutoff": identity_cutoff,
                "sequence_type": "protein",
                "value": seq,
            },
        },
        "request_options": {
            "return_all_hits": False,
            "results_content_type": ["experimental"],
            "sort": [{"sort_by": "score", "direction": "desc"}],
            "scoring_strategy": "sequence",
        },
        "return_type": "polymer_entity",
    }
    response = requests.post("https://search.rcsb.org/rcsbsearch/v2/query", json=payload, timeout=60)
    response.raise_for_status()
    return response.json().get("result_set", [])[:top]


def fetch_json(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_pdb_entity(pdb_id: str, entity_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pdb_id = pdb_id.upper()
    entry = fetch_json(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}")
    entity = fetch_json(f"https://data.rcsb.org/rest/v1/core/polymer_entity/{pdb_id}/{entity_id}")
    return entry, entity


def polymer_entity_ids(pdb_id: str) -> list[str]:
    entry = fetch_json(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id.upper()}")
    return entry.get("rcsb_entry_container_identifiers", {}).get("polymer_entity_ids", [])


def entity_sequence(entity: dict[str, Any]) -> str:
    raw = entity.get("entity_poly", {}).get("pdbx_seq_one_letter_code_can") or entity.get("entity_poly", {}).get("pdbx_seq_one_letter_code") or ""
    return normalize_sequence(raw)


def hit_from_entity(query: str, pdb_id: str, entity_id: str, search_score: float | None = None) -> PdbHit:
    entry, entity = get_pdb_entity(pdb_id, entity_id)
    seq = entity_sequence(entity)
    ids = entity.get("rcsb_polymer_entity_container_identifiers", {})
    refs = ids.get("reference_sequence_identifiers") or []
    uniprot_refs = sorted({r.get("database_accession") for r in refs if r.get("database_name") == "UniProt" and r.get("database_accession")})
    resolution_values = entry.get("rcsb_entry_info", {}).get("resolution_combined") or []
    method = None
    if entry.get("exptl"):
        method = entry["exptl"][0].get("method")
    alignment = align_sequences(query, seq)
    title = entry.get("struct", {}).get("title")
    description = entity.get("rcsb_polymer_entity", {}).get("pdbx_description")
    flags = interpretation_flags(title, description, refs, alignment)
    return PdbHit(
        pdb_id=pdb_id.upper(),
        entity_id=str(entity_id),
        search_score=search_score,
        title=title,
        description=description,
        method=method,
        resolution=float(resolution_values[0]) if resolution_values else None,
        chains=ids.get("auth_asym_ids") or ids.get("asym_ids") or [],
        sequence_length=len(seq),
        uniprot_refs=uniprot_refs,
        sifts_refs=refs,
        alignment=alignment,
        flags=flags,
    )


def interpretation_flags(title: str | None, description: str | None, refs: list[dict[str, Any]], aln: AlignmentStats) -> list[str]:
    text = f"{title or ''} {description or ''}".lower()
    flags = []
    if aln.query_coverage >= 0.99 and aln.identity >= 0.99:
        flags.append("complete_or_near_complete_sequence_match")
    elif aln.query_coverage < 0.8:
        flags.append("partial_sequence_match")
    if not refs:
        flags.append("no_sifts_uniprot_reference_for_entity")
    if any(word in text for word in ["design", "designed", "engineered", "variant", "de novo", "kemp", "retro-aldol"]):
        flags.append("designed_engineered_or_variant_construct")
    if any(word in text for word in ["fusion", "chimera", "lysozyme", "endolysin"]):
        flags.append("fusion_or_chimeric_construct")
    return flags



def fetch_uniprot_json(accession: str) -> dict[str, Any] | None:
    try:
        return fetch_json(f"https://rest.uniprot.org/uniprotkb/{accession}.json")
    except Exception as exc:
        print(f"Warning: could not fetch UniProt {accession}: {exc}")
        return None


def uniprot_summary(accession: str, data: dict[str, Any]) -> dict[str, Any]:
    protein = data.get("proteinDescription", {})
    recommended = protein.get("recommendedName", {})
    submission = protein.get("submissionNames", [{}])
    name = recommended.get("fullName", {}).get("value") or submission[0].get("fullName", {}).get("value")
    genes = []
    for gene in data.get("genes", []) or []:
        value = gene.get("geneName", {}).get("value")
        if value:
            genes.append(value)
    ec_numbers = []
    for source in [recommended, *protein.get("alternativeNames", [])]:
        for ec in source.get("ecNumbers", []) or []:
            if ec.get("value"):
                ec_numbers.append(ec["value"])
    comments = data.get("comments", []) or []
    functions = [text.get("value") for c in comments if c.get("commentType") == "FUNCTION" for text in c.get("texts", []) if text.get("value")]
    catalytic = []
    for c in comments:
        if c.get("commentType") == "CATALYTIC ACTIVITY":
            reaction = c.get("reaction", {})
            if reaction.get("name"):
                catalytic.append(reaction["name"])
    ptm_comments = [text.get("value") for c in comments if c.get("commentType") in {"PTM", "SUBCELLULAR LOCATION"} for text in c.get("texts", []) if text.get("value")]
    features = data.get("features", []) or []
    interesting_types = {"Active site", "Binding site", "Site", "Modified residue", "Glycosylation", "Disulfide bond", "Mutagenesis", "Natural variant", "Topological domain", "Transmembrane"}
    selected_features = []
    for ft in features:
        ftype = ft.get("type")
        if ftype not in interesting_types:
            continue
        loc = ft.get("location", {})
        start = loc.get("start", {}).get("value")
        end = loc.get("end", {}).get("value")
        selected_features.append({
            "type": ftype,
            "start": start,
            "end": end,
            "description": ft.get("description"),
        })
    return {
        "accession": accession,
        "id": data.get("uniProtkbId"),
        "protein_name": name,
        "genes": sorted(set(genes)),
        "organism": data.get("organism", {}).get("scientificName"),
        "ec_numbers": sorted(set(ec_numbers)),
        "function": functions[:3],
        "catalytic_activity": catalytic[:3],
        "ptm_comments": ptm_comments[:3],
        "features": selected_features[:40],
        "uniprot_url": f"https://www.uniprot.org/uniprotkb/{accession}",
        "brenda_url": f"https://www.brenda-enzymes.org/enzyme.php?ecno={ec_numbers[0]}" if ec_numbers else None,
    }


def fetch_alphafold_summary(accession: str) -> dict[str, Any] | None:
    try:
        response = requests.get(f"https://alphafold.ebi.ac.uk/api/prediction/{accession}", timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        items = response.json()
        if not items:
            return None
        item = items[0]
        return {
            "accession": accession,
            "model_url": item.get("pdbUrl"),
            "pae_url": item.get("paeDocUrl"),
            "cif_url": item.get("cifUrl"),
            "version": item.get("latestVersion"),
            "page_url": f"https://alphafold.ebi.ac.uk/entry/{accession}",
        }
    except Exception as exc:
        print(f"Warning: could not fetch AlphaFold {accession}: {exc}")
        return None


def fetch_nonpolymer_ligands(pdb_id: str) -> list[dict[str, Any]]:
    try:
        entry = fetch_json(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id.upper()}")
        ids = entry.get("rcsb_entry_container_identifiers", {}).get("nonpolymer_entity_ids", []) or []
        ligands = []
        for entity_id in ids:
            try:
                nonpoly = fetch_json(f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{pdb_id.upper()}/{entity_id}")
                comp = nonpoly.get("pdbx_entity_nonpoly", {}).get("comp_id")
                name = nonpoly.get("pdbx_entity_nonpoly", {}).get("name") or nonpoly.get("rcsb_nonpolymer_entity", {}).get("pdbx_description")
                if comp:
                    ligands.append({"entity_id": entity_id, "comp_id": comp, "name": name})
            except Exception:
                continue
        return ligands
    except Exception:
        return []


def fetch_entry_polymer_components(pdb_id: str, query_entity_id: str | None = None) -> list[dict[str, Any]]:
    """Return all polymer entities in a PDB entry with their SIFTS/UniProt refs.

    RCSB structure pages often link to UniProt accessions that belong to peptide
    partners or fusion partners, not necessarily to the query polymer entity.
    Reporting the whole entry prevents the misleading statement that "the PDB has
    no UniProt" when the correct interpretation is "the query entity has no
    UniProt, but another polymer entity in the same structure does".
    """
    components = []
    try:
        entity_ids = polymer_entity_ids(pdb_id)
    except Exception:
        return components
    for entity_id in entity_ids:
        try:
            _, entity = get_pdb_entity(pdb_id, entity_id)
        except Exception:
            continue
        ids = entity.get("rcsb_polymer_entity_container_identifiers", {})
        refs = ids.get("reference_sequence_identifiers") or []
        components.append({
            "pdb_id": pdb_id.upper(),
            "entity_id": str(entity_id),
            "is_query_entity": str(entity_id) == str(query_entity_id),
            "description": entity.get("rcsb_polymer_entity", {}).get("pdbx_description"),
            "chains": ids.get("auth_asym_ids") or ids.get("asym_ids") or [],
            "sequence_length": len(entity_sequence(entity)),
            "uniprot_refs": [
                {
                    "accession": ref.get("database_accession"),
                    "database_name": ref.get("database_name"),
                    "entity_sequence_coverage": ref.get("entity_sequence_coverage"),
                    "reference_sequence_coverage": ref.get("reference_sequence_coverage"),
                    "provenance_source": ref.get("provenance_source"),
                }
                for ref in refs
                if ref.get("database_name") == "UniProt" and ref.get("database_accession")
            ],
        })
    return components


def fetch_instance_annotations(pdb_id: str, chain_id: str | None) -> dict[str, Any]:
    if not chain_id:
        return {}
    try:
        inst = fetch_json(f"https://data.rcsb.org/rest/v1/core/polymer_entity_instance/{pdb_id.upper()}/{chain_id}")
    except Exception:
        return {}
    features = inst.get("rcsb_polymer_instance_feature", []) or []
    summary = inst.get("rcsb_polymer_instance_feature_summary", []) or []
    secondary = []
    domains = []
    sites = []
    for ft in features:
        ftype = ft.get("type") or ""
        source = ft.get("provenance_source") or ""
        positions = ft.get("feature_positions", []) or []
        ranges = [format_range(pos.get("beg_seq_id"), pos.get("end_seq_id")) for pos in positions]
        item = {
            "type": ftype,
            "source": source,
            "id": ft.get("feature_id"),
            "name": ft.get("name"),
            "ranges": [r for r in ranges if r],
        }
        if ftype.startswith(("HELIX", "SHEET", "TURN", "BEND")) or source in {"PROMOTIF", "DSSP"}:
            secondary.append(item)
        elif source in {"CATH", "ECOD", "SCOPe", "SCOP", "SCOP2", "SCOP2B", "Pfam"} or ftype in {"CATH", "ECOD", "SCOP", "SCOP2B_SUPERFAMILY"}:
            props = {}
            for prop in ft.get("additional_properties", []) or []:
                props[prop.get("name")] = prop.get("values")
            item["properties"] = props
            domains.append(item)
        elif any(word in ftype.upper() for word in ["SITE", "BIND", "ACTIVE", "MOTIF"]):
            sites.append(item)
    ligand_neighbors = []
    for lig in inst.get("rcsb_ligand_neighbors", []) or []:
        comp = lig.get("ligand_comp_id") or lig.get("comp_id")
        if comp:
            ligand_neighbors.append({"comp_id": comp, "details": lig})
    return {
        "chain_id": chain_id,
        "secondary_features": secondary[:30],
        "secondary_summary": summary,
        "domain_annotations": domains[:20],
        "site_annotations": sites[:20],
        "ligand_neighbors": ligand_neighbors[:20],
    }


def format_range(start: Any, end: Any) -> str | None:
    if start is None and end is None:
        return None
    if start == end or end is None:
        return str(start)
    return f"{start}-{end}"


def enrich_hit_dict(hit: PdbHit) -> dict[str, Any]:
    data = pdb_hit_to_dict(hit)
    first_chain = hit.chains[0] if hit.chains else None
    data["instance_annotations"] = fetch_instance_annotations(hit.pdb_id, first_chain)
    data["nonpolymer_ligands"] = fetch_nonpolymer_ligands(hit.pdb_id)
    data["entry_polymer_components"] = fetch_entry_polymer_components(hit.pdb_id, hit.entity_id)
    data["pdb_url"] = f"https://www.rcsb.org/structure/{hit.pdb_id}"
    return data


def recommended_pdb_hit(hits: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not hits:
        return None
    def rank(hit: dict[str, Any]) -> tuple[int, float, float, float]:
        aln = hit.get("alignment", {})
        exact = int(aln.get("query_coverage", 0) >= 0.99 and aln.get("identity", 0) >= 0.99)
        high = int(aln.get("query_coverage", 0) >= 0.9 and aln.get("identity", 0) >= 0.7)
        resolution = hit.get("resolution")
        res_score = -float(resolution) if resolution is not None else -999.0
        return (exact, high, aln.get("identity", 0), res_score)
    return sorted(hits, key=rank, reverse=True)[0]


def collect_uniprot_annotations(hits: list[dict[str, Any]], recommended: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    accession_sources: dict[str, dict[str, Any]] = {}
    recommended_key = (recommended or {}).get("pdb_id"), (recommended or {}).get("entity_id")
    for hit in hits:
        hit_key = hit.get("pdb_id"), hit.get("entity_id")
        for ref in hit.get("sifts_refs", []) or []:
            if ref.get("database_name") != "UniProt" or not ref.get("database_accession"):
                continue
            acc = ref["database_accession"]
            item = accession_sources.setdefault(acc, {
                "accession": acc,
                "from_recommended_pdb": False,
                "max_entity_sequence_coverage": 0.0,
                "max_reference_sequence_coverage": 0.0,
                "source_hits": [],
            })
            if hit_key == recommended_key:
                item["from_recommended_pdb"] = True
            item["max_entity_sequence_coverage"] = max(item["max_entity_sequence_coverage"], float(ref.get("entity_sequence_coverage") or 0.0))
            item["max_reference_sequence_coverage"] = max(item["max_reference_sequence_coverage"], float(ref.get("reference_sequence_coverage") or 0.0))
            source = f"{hit.get('pdb_id')} entity {hit.get('entity_id')} ({hit.get('description')})"
            if source not in item["source_hits"]:
                item["source_hits"].append(source)
    ordered = sorted(
        accession_sources.values(),
        key=lambda x: (x["from_recommended_pdb"], x["max_entity_sequence_coverage"], x["max_reference_sequence_coverage"]),
        reverse=True,
    )
    summaries = []
    for source in ordered[:5]:
        acc = source["accession"]
        data = fetch_uniprot_json(acc)
        if data:
            summary = uniprot_summary(acc, data)
            summary.update(source)
            summary["alphafold"] = fetch_alphafold_summary(acc)
            summaries.append(summary)
    return summaries


def collect_entry_component_annotations(recommended: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not recommended:
        return []
    summaries = []
    for component in recommended.get("entry_polymer_components", []) or []:
        for ref in component.get("uniprot_refs", []) or []:
            accession = ref.get("accession")
            if not accession:
                continue
            data = fetch_uniprot_json(accession)
            if not data:
                continue
            summary = uniprot_summary(accession, data)
            summary.update({
                "pdb_id": component.get("pdb_id"),
                "entity_id": component.get("entity_id"),
                "is_query_entity": component.get("is_query_entity"),
                "component_description": component.get("description"),
                "component_chains": component.get("chains") or [],
                "component_sequence_length": component.get("sequence_length"),
                "entity_sequence_coverage": ref.get("entity_sequence_coverage"),
                "reference_sequence_coverage": ref.get("reference_sequence_coverage"),
                "provenance_source": ref.get("provenance_source"),
            })
            summaries.append(summary)
    return sorted(
        summaries,
        key=lambda u: (u.get("is_query_entity", False), u.get("entity_sequence_coverage") or 0.0),
        reverse=True,
    )


def primary_uniprot(result: dict[str, Any]) -> dict[str, Any] | None:
    uniprots = result.get("uniprot", [])
    if not uniprots:
        return None
    return sorted(
        uniprots,
        key=lambda u: (u.get("from_recommended_pdb", False), u.get("max_entity_sequence_coverage", 0.0), u.get("max_reference_sequence_coverage", 0.0)),
        reverse=True,
    )[0]

def is_fusion_or_chimera(result: dict[str, Any]) -> bool:
    best = result.get("recommended_pdb") or {}
    refs = best.get("uniprot_refs", []) or []
    flags = set(best.get("flags", []) or [])
    return "fusion_or_chimeric_construct" in flags or len(refs) > 1


def fusion_components(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Return UniProt/PDB components that should be discussed separately.

    For fusion/chimeric constructs, RCSB/SIFTS commonly maps one polymer entity to
    more than one UniProt accession. Those mappings identify biological components
    of the construct even when residue-level ranges are not exposed by the REST
    endpoint used here.
    """
    if not is_fusion_or_chimera(result):
        return []
    best = result.get("recommended_pdb") or {}
    recommended_refs = set(best.get("uniprot_refs", []) or [])
    components = []
    for up in result.get("uniprot", []) or []:
        component_role = "recommended PDB entity component" if up.get("accession") in recommended_refs or up.get("from_recommended_pdb") else "related PDB component"
        components.append({
            "accession": up.get("accession"),
            "protein_name": up.get("protein_name"),
            "genes": up.get("genes") or [],
            "organism": up.get("organism"),
            "ec_numbers": up.get("ec_numbers") or [],
            "entity_coverage": up.get("max_entity_sequence_coverage"),
            "reference_coverage": up.get("max_reference_sequence_coverage"),
            "role": component_role,
            "function": (up.get("function") or [None])[0],
            "catalytic_activity": (up.get("catalytic_activity") or [None])[0],
            "uniprot_url": up.get("uniprot_url"),
            "brenda_url": up.get("brenda_url"),
            "source_hits": up.get("source_hits", []),
        })
    return sorted(
        components,
        key=lambda c: (c["role"] == "recommended PDB entity component", c.get("entity_coverage") or 0.0),
        reverse=True,
    )


def summarize_fusion_components(result: dict[str, Any]) -> str:
    components = fusion_components(result)
    if not components:
        return "No fusion/chimeric construct was detected from RCSB/SIFTS metadata."
    parts = []
    for comp in components:
        gene = ", ".join(comp.get("genes") or []) or "gene not annotated"
        ec = ", ".join(comp.get("ec_numbers") or []) or "no EC"
        parts.append(
            f"{comp.get('accession')} ({comp.get('protein_name') or 'unnamed'}, {gene}; "
            f"entity coverage {pct(comp.get('entity_coverage'))}, reference coverage {pct(comp.get('reference_coverage'))}, {ec})"
        )
    return "Fusion/chimeric construct detected. Discuss these components separately: " + "; ".join(parts)


def markdown_fusion_section(result: dict[str, Any]) -> list[str]:
    components = fusion_components(result)
    if not components:
        return []
    best = result.get("recommended_pdb") or {}
    ann = best.get("instance_annotations", {})
    lines = [
        "## Fusion/chimeric construct components",
        "",
        "RCSB/SIFTS maps the recommended polymer entity to more than one UniProt component, or the PDB metadata marks it as a fusion/chimeric construct. Interpret each component separately before assigning function, active sites, EC numbers or variants.",
        "",
        f"Recommended structure: {best.get('pdb_id')} entity {best.get('entity_id')} ({best.get('description')}).",
        "",
    ]
    for comp in components:
        lines += [
            f"### {comp.get('accession')} - {comp.get('protein_name') or 'unnamed component'}",
            "",
            f"- Role in construct: {comp.get('role')}",
            f"- Gene(s): {', '.join(comp.get('genes') or []) or 'not reported'}",
            f"- Organism: {comp.get('organism') or 'not reported'}",
            f"- Entity coverage in the fused polymer: {pct(comp.get('entity_coverage'))}",
            f"- Reference-sequence coverage: {pct(comp.get('reference_coverage'))}",
            f"- EC number(s): {', '.join(comp.get('ec_numbers') or []) or 'none reported'}",
            f"- UniProt: {comp.get('uniprot_url') or 'not available'}",
            f"- BRENDA: {comp.get('brenda_url') or 'not applicable without an EC number'}",
            f"- Function to discuss for this component: {comp.get('function') or 'no concise function retrieved; use literature/PDB context'}",
        ]
        if comp.get("catalytic_activity"):
            lines.append(f"- Catalytic activity for this component: {comp.get('catalytic_activity')}")
        lines.append("")
    lines += [
        "### Domain and range evidence from the PDB entity",
        "",
        f"- Domain annotations exposed by RCSB for the inspected chain: {summarize_domain_annotations(ann.get('domain_annotations', []))}",
        f"- Secondary-structure features exposed by RCSB for the inspected chain: {summarize_secondary_features(ann.get('secondary_features', []))}",
        "- If RCSB/SIFTS does not expose exact residue ranges for every UniProt component through this report, determine the boundaries in ChimeraX or by aligning the fused polymer sequence against each UniProt sequence separately.",
        "- Do not transfer the EC number, active site, variants or PTMs from a fusion partner to the other component.",
        "",
    ]
    return lines

def answer_guidance(result: dict[str, Any]) -> dict[str, Any]:
    best = result.get("recommended_pdb")
    uniprots = result.get("uniprot", [])
    features = result.get("features", {})
    guidance = {}
    best_entity_has_uniprot = bool((best or {}).get("uniprot_refs"))
    entry_components = result.get("pdb_entry_uniprot_components", [])
    partner_components = [c for c in entry_components if not c.get("is_query_entity")]
    if uniprots:
        u = primary_uniprot(result) or uniprots[0]
        source_note = "linked to the recommended PDB entity" if u.get("from_recommended_pdb") else "found in related PDB hits, not in the recommended entity"
        if not best_entity_has_uniprot and partner_components:
            partner_text = "; ".join(
                f"{c.get('accession')} ({c.get('protein_name') or c.get('component_description')}, PDB entity {c.get('entity_id')}, chains {', '.join(c.get('component_chains') or [])}, entity coverage {pct(c.get('entity_sequence_coverage'))})"
                for c in partner_components[:5]
            )
            related_text = "; ".join(
                f"{x['accession']} ({x.get('protein_name') or 'unnamed'}, related-hit entity coverage {pct(x.get('max_entity_sequence_coverage'))})"
                for x in uniprots[:5]
            )
            guidance["protein_identity"] = (
                "No direct UniProt reference was found for the best matching query polymer entity. "
                f"The selected PDB entry contains UniProt-mapped partner entity/entities: {partner_text}. "
                f"Related PDB hits also suggest this biological context: {related_text}. "
                "Use the partner UniProt record to discuss the bound peptide or biological partner, not as the identity of the designed/query polymer."
            )
        elif len(uniprots) > 1:
            refs = "; ".join(f"{x['accession']} ({x.get('protein_name') or 'unnamed'}, entity coverage {pct(x.get('max_entity_sequence_coverage'))})" for x in uniprots)
            guidance["protein_identity"] = f"Candidate UniProt records: {refs}. Primary suggestion: {u['accession']} ({source_note}). Gene: {', '.join(u.get('genes') or []) or 'not annotated in fetched record'}. Check fusion partners before assigning function."
        else:
            guidance["protein_identity"] = f"Candidate UniProt {u['accession']} ({u.get('protein_name') or 'name not available'}), {source_note}. Gene: {', '.join(u.get('genes') or []) or 'not annotated in fetched record'}."
        ec_text = ", ".join(u.get("ec_numbers") or []) or "No EC number found in the selected UniProt record; do not force an enzyme classification."
        function_text = " ".join(u.get("function") or []) or "No concise UniProt function text was retrieved; use literature or PDB/structure context."
        best_flags = set((result.get("recommended_pdb") or {}).get("flags", []))
        if not u.get("from_recommended_pdb"):
            ec_text = f"Context only from a related/non-recommended UniProt mapping: {ec_text}"
            function_text = f"Context only from a related/non-recommended UniProt mapping: {function_text} Do not assign this function directly to the input sequence without explaining the alignment and construct relationship."
        elif "designed_engineered_or_variant_construct" in best_flags:
            if u.get("ec_numbers"):
                ec_text = f"{ec_text} (check whether this EC number belongs to the natural scaffold/reference or to the engineered construct)."
            function_text = f"{function_text} For engineered/designed constructs, distinguish natural scaffold function from the function intended by the construct."
        guidance["ec"] = ec_text
        guidance["function"] = function_text
    else:
        if partner_components:
            partner_text = "; ".join(
                f"{c.get('accession')} ({c.get('protein_name') or c.get('component_description')}, PDB entity {c.get('entity_id')}, chains {', '.join(c.get('component_chains') or [])}, entity coverage {pct(c.get('entity_sequence_coverage'))})"
                for c in partner_components[:5]
            )
            guidance["protein_identity"] = (
                "No direct UniProt reference was found for the best matching query polymer entity. "
                f"The same PDB entry does contain UniProt-mapped polymer partner(s): {partner_text}. "
                "Discuss these as complex partners, peptide partners or fusion partners, not as the identity of the query entity unless the sequence alignment supports it."
            )
        else:
            guidance["protein_identity"] = "No direct UniProt reference was found for the best PDB polymer entity. Treat the sequence as a construct/design unless another search justifies a natural protein assignment."
        guidance["ec"] = "No EC number can be assigned from UniProt/PDB metadata."
        guidance["function"] = "Function must be derived from the PDB title, construct description, homologs, or literature; mark the evidence source explicitly."
    if best:
        aln = best.get("alignment", {})
        guidance["structure_choice"] = f"Recommended PDB: {best['pdb_id']} entity {best['entity_id']} ({best.get('description')}). Query coverage {pct(aln.get('query_coverage'))}, identity {pct(aln.get('identity'))}, resolution {fmt(best.get('resolution'))} Å."
        ligs = best.get("nonpolymer_ligands", [])
        guidance["ligands"] = "; ".join(f"{l.get('comp_id')} ({l.get('name')})" for l in ligs[:10]) or "No non-polymer ligands were retrieved from this PDB entry. Check peptide/polymer partners separately."
        ann = best.get("instance_annotations", {})
        guidance["domains"] = summarize_domain_annotations(ann.get("domain_annotations", []))
        guidance["secondary"] = summarize_secondary_features(ann.get("secondary_features", []))
    else:
        guidance["structure_choice"] = "No experimental PDB hit was retrieved; use AlphaFold if a reliable UniProt accession is known, or run a structure prediction workflow."
        guidance["ligands"] = "No PDB ligands available."
        guidance["domains"] = "No PDB domain annotations available."
        guidance["secondary"] = "No PDB secondary-structure annotations available; inspect the predicted structure in ChimeraX."
    guidance["construct_features"] = summarize_construct_features(features)
    guidance["fusion_components"] = summarize_fusion_components(result)
    return guidance


def summarize_domain_annotations(domains: list[dict[str, Any]]) -> str:
    if not domains:
        return "No CATH/ECOD/SCOP/Pfam annotations were retrieved for the inspected chain; check CATH/ECOD manually if needed."
    parts = []
    for d in domains[:8]:
        ranges = ",".join(d.get("ranges", []) or [])
        parts.append(f"{d.get('source') or d.get('type')} {d.get('id')} {d.get('name')} ({ranges})")
    return "; ".join(parts)


def summarize_secondary_features(features: list[dict[str, Any]]) -> str:
    if not features:
        return "No secondary-structure features were retrieved from RCSB for the inspected chain; use ChimeraX/DSSP."
    counts: dict[str, int] = {}
    examples = []
    for f in features:
        key = f.get("name") or f.get("type") or "feature"
        counts[key] = counts.get(key, 0) + 1
        if len(examples) < 8:
            examples.append(f"{key} {','.join(f.get('ranges', []) or [])}")
    return ", ".join(f"{k}: {v}" for k, v in counts.items()) + "; examples: " + "; ".join(examples)


def summarize_construct_features(features: dict[str, Any]) -> str:
    parts = []
    if features.get("tags"):
        parts.append("tags: " + format_tags(features["tags"]))
    if features.get("unknown_count"):
        parts.append(f"non-canonical residues: {features['unknown_positions']}")
    if features.get("cysteine_count"):
        parts.append(f"cysteines at {features['cysteine_positions']}")
    return "; ".join(parts) if parts else "No common purification tag, ambiguous residue or cysteine-specific warning was detected from the sequence alone."
def analyse_record(record: dict[str, str], top_pdb: int, identity_cutoff: float, evalue_cutoff: float) -> dict[str, Any]:
    seq = record["sequence"]
    features = sequence_features(seq)
    hits: list[dict[str, Any]] = []
    try:
        search_hits = rcsb_sequence_search(seq, top=top_pdb, identity_cutoff=identity_cutoff, evalue_cutoff=evalue_cutoff)
        for raw_hit in search_hits:
            identifier = raw_hit.get("identifier", "")
            if "_" not in identifier:
                continue
            pdb_id, entity_id = identifier.split("_", 1)
            try:
                hits.append(enrich_hit_dict(hit_from_entity(seq, pdb_id, entity_id, raw_hit.get("score"))))
            except Exception as exc:
                print(f"Warning: could not fetch {identifier}: {exc}")
    except Exception as exc:
        print(f"Warning: RCSB sequence search failed for {record['id']}: {exc}")
    result = {
        "id": record["id"],
        "description": record["description"],
        "data_sources": DATA_SOURCES,
        "features": features,
        "pdb_hits": hits,
    }
    result["recommended_pdb"] = recommended_pdb_hit(hits)
    result["uniprot"] = collect_uniprot_annotations(hits, result["recommended_pdb"])
    result["pdb_entry_uniprot_components"] = collect_entry_component_annotations(result["recommended_pdb"])
    result["guidance"] = answer_guidance(result)
    return result

def pdb_hit_to_dict(hit: PdbHit) -> dict[str, Any]:
    data = asdict(hit)
    data["alignment"] = asdict(hit.alignment)
    return data


def write_outputs(results: list[dict[str, Any]], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary_csv(results, output_dir / "summary.csv")
    for result in results:
        (reports_dir / f"{safe_name(result['id'])}.md").write_text(markdown_report(result), encoding="utf-8")


def write_summary_csv(results: list[dict[str, Any]], path: str | Path) -> None:
    import pandas as pd

    rows = []
    for result in results:
        features = result["features"]
        best = result.get("recommended_pdb") or (result["pdb_hits"][0] if result["pdb_hits"] else None)
        aln = best.get("alignment") if best else {}
        uniprot = result.get("uniprot", [])
        first_up = primary_uniprot(result) or (uniprot[0] if uniprot else {})
        rows.append({
            "seq_id": result["id"],
            "length": features["length"],
            "unknown_count": features["unknown_count"],
            "tags": ";".join(f"{t['type']}:{t['start']}-{t['end']}" for t in features["tags"]),
            "cysteine_count": features["cysteine_count"],
            "recommended_pdb": best.get("pdb_id") if best else None,
            "recommended_entity": best.get("entity_id") if best else None,
            "recommended_description": best.get("description") if best else None,
            "recommended_resolution": best.get("resolution") if best else None,
            "recommended_query_coverage": aln.get("query_coverage") if aln else None,
            "recommended_identity": aln.get("identity") if aln else None,
            "uniprot_accession": first_up.get("accession"),
            "gene": ";".join(first_up.get("genes", [])) if first_up else None,
            "ec_numbers": ";".join(first_up.get("ec_numbers", [])) if first_up else None,
            "pdb_entry_uniprot_components": ";".join(
                f"{c.get('entity_id')}:{c.get('accession')}:{'query' if c.get('is_query_entity') else 'partner'}"
                for c in result.get("pdb_entry_uniprot_components", [])
            ),
            "pdb_ligands": ";".join(f"{l.get('comp_id')}" for l in (best.get("nonpolymer_ligands", []) if best else [])),
            "fusion_components": ";".join(f"{c.get('accession')}:{pct(c.get('entity_coverage'))}" for c in fusion_components(result)),
            "flags": ";".join(best.get("flags", [])) if best else None,
        })
    pd.DataFrame(rows).to_csv(path, index=False)


def markdown_report(result: dict[str, Any]) -> str:
    f = result["features"]
    guidance = result.get("guidance", {})
    lines = [f"# Protein sequence report: {result['id']}", "", f"Description: `{result['description']}`", ""]
    lines += ["## Data provenance", ""]
    lines += ["This report is generated from local sequence analysis plus public bioinformatics APIs/databases. No generative model or conversational AI service is queried by these scripts.", ""]
    for source in result.get("data_sources", DATA_SOURCES):
        lines.append(f"- {source['name']} ({source['kind']}): {source['use']}. {source['url']}")
    lines.append("")
    lines += ["## Direct answers to investigate", ""]
    lines += [
        "### 1. Protein identity, structure and function",
        "",
        f"- UniProt/gene: {guidance.get('protein_identity')}",
        f"- EC/BRENDA: {guidance.get('ec')}",
        f"- PDB choice: {guidance.get('structure_choice')}",
        f"- Function summary: {guidance.get('function')}",
        f"- Construct features to mention: {guidance.get('construct_features')}",
        f"- Fusion/chimeric components: {guidance.get('fusion_components')}",
        "",
        "### 2. Structural work to do in ChimeraX",
        "",
        f"- Secondary structure from PDB annotations: {guidance.get('secondary')}",
        "- In ChimeraX, verify secondary structure visually and with commands such as `dssp`, `hbonds restrict both`, and `contacts`/`clashes` around the selected elements.",
        f"- Fold/domain annotations: {guidance.get('domains')}",
        "- For supersecondary structure, inspect repeated helix/strand arrangements, interfaces between elements, hydrogen bonds and van der Waals contacts; the report gives ranges to start from when RCSB exposes them.",
        "- For quaternary structure, compare the asymmetric unit, biological assembly and chain list in RCSB before drawing conclusions.",
        "",
        "### 3. Functional interpretation",
        "",
        f"- Ligands/cofactors/inhibitors in the recommended PDB: {guidance.get('ligands')}",
        "- Active-site and binding-site residues should be taken from UniProt features, PDB ligands/neighbors, catalytic literature, or conserved-residue alignments; then remap them to the input-sequence numbering.",
        "- Post-translational modifications and variants must be checked against the exact residues present in the input sequence; do not transfer them from a different isoform or homolog without an alignment.",
        "- Relate sequence-structure-function by naming concrete regions, residue numbers, structural elements and the evidence source for each claim.",
        "",
    ]
    lines += ["## Sequence descriptors", ""]
    lines += [
        f"- Length: {f['length']} aa",
        f"- Unknown or non-canonical residues: {f['unknown_count']} ({f['unknown_positions']})",
        f"- Molecular weight: {fmt(f.get('molecular_weight_da'))} Da",
        f"- Isoelectric point: {fmt(f.get('isoelectric_point'))}",
        f"- GRAVY: {fmt(f.get('gravy'))}",
        f"- Estimated helix/turn/sheet fractions from sequence composition: {fmt(f.get('helix_fraction_estimate'))} / {fmt(f.get('turn_fraction_estimate'))} / {fmt(f.get('sheet_fraction_estimate'))}",
        f"- Cysteines: {f['cysteine_count']} ({f['cysteine_positions']})",
        f"- N-glycosylation motif starts: {f['n_glycosylation_motif_positions']}",
        f"- Tags/motifs detected: {format_tags(f['tags'])}",
    ]
    lines += ["", *markdown_fusion_section(result), "## UniProt and functional annotations", ""]
    if not result.get("uniprot"):
        lines.append("No UniProt record was retrieved from PDB/SIFTS references for the candidate structures. This often indicates a designed construct, a variant, or a PDB entry without a canonical UniProt mapping. If a natural protein assignment is required, run an independent UniProt BLAST/search and document the coverage and identity.")
    for up in result.get("uniprot", []):
        lines += [
            f"### {up.get('accession')} ({up.get('id')})",
            "",
            f"- Protein name: {up.get('protein_name')}",
            f"- Gene(s): {', '.join(up.get('genes') or []) or 'not reported'}",
            f"- Organism: {up.get('organism')}",
            f"- EC number(s): {', '.join(up.get('ec_numbers') or []) or 'none reported'}",
            f"- UniProt: {up.get('uniprot_url')}",
            f"- BRENDA lookup: {up.get('brenda_url') or 'not applicable without an EC number'}",
            f"- AlphaFold DB: {(up.get('alphafold') or {}).get('page_url') or 'not found or not checked'}",
            f"- Mapping source: {'recommended PDB entity' if up.get('from_recommended_pdb') else 'related/non-recommended PDB hit'}; entity coverage {pct(up.get('max_entity_sequence_coverage'))}; reference coverage {pct(up.get('max_reference_sequence_coverage'))}",
            f"- Source hit(s): {'; '.join(up.get('source_hits', []))}",
            "",
        ]
        if up.get("function"):
            lines += ["Function comments:"] + [f"- {text}" for text in up["function"]] + [""]
        if up.get("catalytic_activity"):
            lines += ["Catalytic activity:"] + [f"- {text}" for text in up["catalytic_activity"]] + [""]
        if up.get("ptm_comments"):
            lines += ["PTM/subcellular comments:"] + [f"- {text}" for text in up["ptm_comments"]] + [""]
        if up.get("features"):
            lines += ["Selected residue features:"]
            for ft in up["features"][:20]:
                lines.append(f"- {ft.get('type')} {format_range(ft.get('start'), ft.get('end'))}: {ft.get('description') or ''}")
            lines.append("")
    lines += ["## UniProt mappings in the selected PDB entry", ""]
    entry_components = result.get("pdb_entry_uniprot_components", [])
    if not entry_components:
        lines.append("No UniProt mapping was retrieved for any polymer entity in the selected PDB entry.")
    else:
        lines.append("These mappings are reported per PDB polymer entity. A UniProt accession mapped to a partner entity is evidence for that partner, not automatically for the input sequence.")
        lines.append("")
        for comp in entry_components:
            role = "query entity" if comp.get("is_query_entity") else "partner/fusion/peptide entity"
            lines += [
                f"- PDB {comp.get('pdb_id')} entity {comp.get('entity_id')} ({role}; chains {', '.join(comp.get('component_chains') or [])}): "
                f"{comp.get('accession')} {comp.get('protein_name') or comp.get('component_description')} "
                f"[entity coverage {pct(comp.get('entity_sequence_coverage'))}; reference coverage {pct(comp.get('reference_sequence_coverage'))}; "
                f"UniProt {comp.get('uniprot_url')}]"
            ]
    lines.append("")
    lines += ["## Best PDB sequence hits", ""]
    if not result["pdb_hits"]:
        lines.append("No RCSB hits were retrieved. If a reliable UniProt accession is known, use AlphaFold DB or run a structure prediction workflow.")
    for i, hit in enumerate(result["pdb_hits"][:10], 1):
        aln = hit["alignment"]
        ann = hit.get("instance_annotations", {})
        lines += [
            f"### {i}. {hit['pdb_id']} entity {hit['entity_id']}",
            "",
            f"- RCSB: {hit.get('pdb_url')}",
            f"- Description: {hit['description']}",
            f"- Title: {hit['title']}",
            f"- Method/resolution: {hit['method']} / {fmt(hit['resolution'])} Å",
            f"- Chains: {', '.join(hit['chains']) if hit['chains'] else 'not reported'}",
            f"- UniProt references for this entity: {', '.join(hit['uniprot_refs']) if hit['uniprot_refs'] else 'none reported'}",
            f"- Query coverage: {pct(aln['query_coverage'])}",
            f"- Entity coverage: {pct(aln['target_coverage'])}",
            f"- Identity over aligned positions: {pct(aln['identity'])}",
            f"- Aligned query region: {aln['query_start']}-{aln['query_end']}",
            f"- Aligned entity region: {aln['target_start']}-{aln['target_end']}",
            f"- Non-polymer ligands: {format_ligands(hit.get('nonpolymer_ligands', []))}",
            f"- Secondary features: {summarize_secondary_features(ann.get('secondary_features', []))}",
            f"- Domain annotations: {summarize_domain_annotations(ann.get('domain_annotations', []))}",
            f"- Interpretation flags: {', '.join(hit['flags']) if hit['flags'] else 'none'}",
            f"- Fusion/chimera handling: {'discuss UniProt/SIFTS components and PDB domain ranges separately' if 'fusion_or_chimeric_construct' in hit.get('flags', []) or len(hit.get('uniprot_refs', [])) > 1 else 'not flagged as fusion/chimera'}",
            "",
        ]
    lines += ["## Evidence checklist", "", "- State whether the protein identity is an exact sequence match, a construct/design, a homolog, or only a partial scaffold.", "- Give PDB code, entity, chain, coverage, identity, method and resolution before using structural conclusions.", "- If multiple PDBs exist, justify the selected one by coverage first, then identity, then resolution and biological relevance/ligand state.", "- If no suitable PDB exists, report AlphaFold/other prediction and its confidence rather than treating it as experimental structure.", "- Separate query polymer, peptide partners, ligands, fusion partners and purification tags.", "- Map functional residues, variants and PTM sites to the input sequence numbering.", "- Mark each functional claim as directly supported by the exact sequence/structure or derived from a homolog/literature source."]
    return "\n".join(lines) + "\n"


def format_ligands(ligands: list[dict[str, Any]]) -> str:
    if not ligands:
        return "none retrieved"
    return "; ".join(f"{l.get('comp_id')} ({l.get('name')})" for l in ligands[:12])

def fmt(value: Any) -> str:
    if value is None:
        return "not available"
    if isinstance(value, float):
        if math.isnan(value):
            return "not available"
        return f"{value:.3f}"
    return str(value)


def pct(value: Any) -> str:
    if value is None:
        return "not available"
    return f"{100 * float(value):.1f}%"


def format_tags(tags: list[dict[str, Any]]) -> str:
    if not tags:
        return "none detected"
    return "; ".join(f"{tag['type']} {tag['start']}-{tag['end']} ({tag['sequence']})" for tag in tags)


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)
