# Importa el mòdul PyMOL
import pymol

# Inicia l'entorn de treball PyMOL
pymol.finish_launching()

# Descarrega les dues proteïnes Ras i RasGAP des de la web (PDB)
pymol.cmd.fetch('5P21')
pymol.cmd.fetch('1WQ1')

# Aplica una representació de cintes a les dues proteïnes
pymol.cmd.show('cartoon', '5P21')
pymol.cmd.show('cartoon', '1WQ1')
quit()
# Realitza la superposició de les dues proteïnes utilitzant l'alineament estructural
# en base als àtoms seleccionats (en aquest cas, les cadenes A de Ras i RasGAP)
pymol.cmd.align('5P21 and chain R', '1WQ1 and chain R')

# Refresca la visualització de la finestra gràfica de PyMOL
pymol.cmd.refresh()

# Pausa per permetre la visualització de les proteïnes superposades
pymol.cmd.png('output.png', width=800, height=600, dpi=300)  # Captura una imatge de la visualització en un fitxer PNG
pymol.cmd.util.mroll()  # Mostra un missatge a la consola

# Tanca l'entorn de treball PyMOL
pymol.cmd.quit()
