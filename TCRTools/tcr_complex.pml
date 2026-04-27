reinitialize

# Carrega estructura
fetch 7phr, async=0

hide everything
show cartoon, all
bg_color white

# ===== DEFINICIO DE CADENES =====
# (les cadenes poden variar segons el PDB)

# TCR chains
select TCR_alpha, chain A
select TCR_beta, chain B

# MHC
select MHC_heavy, chain C
select B2M, chain D

# peptide
select peptide, chain E

# CD3 complex
select CD3_delta, chain F
select CD3_gamma, chain G
select CD3_epsilon1, chain H
select CD3_epsilon2, chain I
select CD3_zeta, chain J+K

# ===== COLORS =====

color marine, TCR_alpha
color cyan, TCR_beta

color green, MHC_heavy
color limon, B2M

color orange, peptide

color red, CD3_delta
color tv_red, CD3_gamma
color lightpink, CD3_epsilon1
color hotpink, CD3_epsilon2
color magenta, CD3_zeta

# ===== VISUALITZACIO =====

show sticks, peptide
set stick_radius, 0.25

# estil
set cartoon_fancy_helices, 1
set antialias, 2
set specular, 0.2
set ray_shadow, 0

# centre
orient

# ===== ETIQUETES =====
# Una sola etiqueta per seleccio, situada al centre de la subunitat.
# Aixo evita etiquetar cada atom CA de la cadena.

set label_size, 18
set label_color, black
set label_bg_color, white
set label_bg_transparency, 0.25
set label_connector, on
set label_connector_color, gray40

pseudoatom lab_TCR_alpha, TCR_alpha
pseudoatom lab_TCR_beta, TCR_beta
pseudoatom lab_MHC_heavy, MHC_heavy
pseudoatom lab_B2M, B2M
pseudoatom lab_peptide, peptide
pseudoatom lab_CD3_delta, CD3_delta
pseudoatom lab_CD3_gamma, CD3_gamma
pseudoatom lab_CD3_epsilon1, CD3_epsilon1
pseudoatom lab_CD3_epsilon2, CD3_epsilon2
pseudoatom lab_CD3_zeta, CD3_zeta

hide nonbonded, lab_*
label lab_TCR_alpha, "TCR alpha"
label lab_TCR_beta, "TCR beta"
label lab_MHC_heavy, "MHC heavy"
label lab_B2M, "B2M"
label lab_peptide, "peptide"
label lab_CD3_delta, "CD3 delta"
label lab_CD3_gamma, "CD3 gamma"
label lab_CD3_epsilon1, "CD3 epsilon 1"
label lab_CD3_epsilon2, "CD3 epsilon 2"
label lab_CD3_zeta, "CD3 zeta"

zoom all, 5
