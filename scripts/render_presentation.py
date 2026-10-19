#!/usr/bin/env python3
"""Compact, editable teaching illustrations; detailed boards remain in diagramas/."""
import argparse
import html
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'assets/presentacion'
INK = '#203b33'
COLORS = {'event': '#ffe1bc', 'pain': '#f9d8d0', 'actor': '#e5dcf1',
          'data': '#dcebdc', 'decision': '#fff0bb', 'workflow': '#d7eaf2',
          'policy': '#fff0bb', 'opportunity': '#fff0bb', 'command': '#d7eaf2'}


class Scene:
    def __init__(self, title, description):
        self.title, self.description, self.parts = title, description, []

    def text(self, x, y, value, size=23, weight=500, color=INK, anchor='start'):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{html.escape(value)}</text>')

    def rect(self, x, y, w, h, fill, stroke='none', radius=12):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def arrow(self, path):
        self.parts.append(f'<path d="{path}" fill="none" stroke="#387363" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"/>')

    def note(self, x, y, w, label, title, kind, h=114, selected=False):
        self.rect(x+3, y+5, w, h, '#203b3312', radius=3)
        self.rect(x, y, w, h, COLORS[kind], '#387363' if selected else '#203b3320', 3)
        self.parts.append(f'<path d="M{x+w-17} {y}h17v17z" fill="#203b3318"/>')
        self.text(x+15, y+24, label, 13, 750)
        for i, line in enumerate(textwrap.wrap(title, max(12, int((w-30)/12)), break_long_words=False)):
            self.text(x+15, y+56+i*26, line, 22, 650)

    def finish(self):
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 650" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(self.title)}</title><desc id="desc">{html.escape(self.description)}</desc>
<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#d4d7ca"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#387363"/></marker></defs>
<rect width="1200" height="650" rx="20" fill="#f6f4ed"/><rect width="1200" height="650" rx="20" fill="url(#dots)"/>
<g font-family="system-ui,-apple-system,Segoe UI,sans-serif">{''.join(self.parts)}</g></svg>\n'''


def render():
    data = json.loads((ROOT/'workshop/discovery.json').read_text())['boards']
    notes = {key: {n['id']: n for n in b['items']} for key, b in data.items()}
    out = {}
    s = Scene('Escuchar, preguntar, aprender', 'La pregunta abre una respuesta del cliente. El coach ayuda a interpretarla y el tablero conserva el aprendizaje.')
    s.text(50, 60, 'UNA CONVERSACIÓN QUE DEJA HUELLA', 18, 750, '#387363')
    for x, title, subtitle, color in [(65, 'Tú', 'Eliges una pregunta', '#fff0bb'), (455, 'Cliente', 'Cuenta lo que sucede', '#e5dcf1'), (845, 'Coach', 'Ayuda a profundizar', '#dcebdc')]:
        s.rect(x, 105, 290, 165, color)
        s.text(x+25, 160, title, 34, 750)
        s.text(x+25, 203, subtitle, 20)
    s.arrow('M370 187H435'); s.arrow('M760 187H825')
    s.note(65, 350, 290, 'PREGUNTA', '¿Qué ocurrió la última vez?', 'decision')
    s.note(455, 350, 290, 'DOLOR', 'No sabemos si se cobró', 'pain')
    s.note(845, 350, 290, 'APRENDIZAJE', 'Ubicar la excepción', 'data')
    s.arrow('M600 282V333')
    s.text(600, 560, 'Cada respuesta añade una pieza al tablero.', 26, 650, anchor='middle')
    out['01-conversacion.svg'] = s.finish()

    s = Scene('Del proceso a su dolor', 'Los eventos se ordenan; personas, datos y dolores se ubican bajo el paso al que pertenecen. El dolor del caso está en la recuperación.')
    s.text(40, 55, 'A · PRIMERO ENTENDER EL PROCESO', 18, 750, '#387363')
    for i, ident in enumerate(['request', 'approved', 'paid', 'booked', 'recovered']):
        x=160+i*204
        s.text(x+90, 105, ['Inicio', 'Decisión', 'Efecto', 'Resultado', 'Excepción'][i], 20, 700, anchor='middle')
        s.note(x, 132, 184, 'EVENTO', notes['A'][ident]['title'], 'event', 135)
        if i<3: s.arrow(f'M{x+186} 198h16')
    for y, label in [(208,'Sucede'), (341,'Actúa'), (474,'Duele')]:
        s.text(28,y,label,18,700)
    s.note(160, 292, 184, 'PERSONA', notes['A']['traveler']['title'], 'actor')
    s.note(364, 292, 184, 'PERSONA', notes['A']['reviewer']['title'], 'actor')
    s.note(976, 292, 184, 'PERSONA', notes['A']['operator']['title'], 'actor')
    s.note(976, 435, 184, 'DOLOR', notes['A']['uncertain']['title'], 'pain')
    s.text(175, 500, '«Se perdió la respuesta. ¿Se reservó y se cobró?»', 25, 650)
    s.text(40, 610, 'A1 dolor → A2 límites → A3 eventos → A4 excepción → A5–A9 contexto', 21, 650, '#387363')
    out['02-proceso.svg'] = s.finish()

    s = Scene('Elegir la oportunidad', 'Cuadrantes de reglas o criterio y disponibilidad de datos. Preparar una reserva se elige con decisión humana: P y H.')
    s.text(40, 55, 'B · CANDIDATAS → DATOS → CUADRANTES → AUTONOMÍA', 18, 750, '#387363')
    for x, title in [(410,'Reglas conocidas'), (890,'Interpretación y criterio')]: s.text(x,104,title,24,700,anchor='middle')
    for y, title in [(232,'Disponibles'), (485,'Por habilitar')]:
        s.text(22,y-25,'DATOS',13,750); s.text(22,y,title,20,650)
    for x,y in [(180,125),(660,125),(180,380),(660,380)]: s.rect(x,y,455,233,'#fffdf7','#c8d2c4')
    s.note(200,153,330,'AUTOMATIZACIÓN',notes['B']['form']['title'],'workflow',125)
    s.note(680,145,200,'E · EXPLORAR',notes['B']['readhelper']['title'],'opportunity',139)
    s.note(895,145,200,'P + H · ELEGIDA',notes['B']['bookingagent']['title'],'opportunity',139,True)
    s.text(682,325,'La persona decide; el agente prepara.',21,650)
    s.text(206,477,'Primero integrar los datos.',22)
    s.note(680,411,330,'DATOS POR HABILITAR',notes['B']['exceptions']['title'],'pain',135)
    out['03-oportunidad.svg'] = s.finish()

    s = Scene('Un flujo con una decisión humana', 'La persona solicita. El agente consulta y propone. La persona aprueba. La API valida y ejecuta. La respuesta incierta se recupera sin duplicar.')
    s.text(40,55,'C · CADA ACCIÓN EN SU CARRIL',18,750,'#387363')
    for y,label in [(100,'Persona'),(265,'Agente'),(430,'API / datos')]:
        s.rect(20,y,1160,148,'#fffdf7','#d4d7ca')
        s.text(40,y+45,label,21,750)
    s.arrow('M355 191V245H435V290')
    s.arrow('M575 330H620V198H660')
    s.arrow('M805 207V493H865')
    s.note(210,115,180,'INTENCIÓN','Solicitar reserva','event')
    s.note(325,280,260,'CONSULTA Y PROPUESTA','Preparar la decisión','workflow')
    s.note(660,115,220,'P + H','Aprobar o rechazar','decision')
    s.note(865,445,280,'ACCIÓN AUTORIZADA','Validar y ejecutar','data')
    s.text(210,494,'¿Respuesta incierta?',23,700)
    s.text(210,532,'Consultar el estado y recuperar.',22)
    s.arrow('M850 520H630')
    s.text(40,620,'Rechazar termina sin escritura. Cancelar requiere una aprobación nueva.',21,650,'#387363')
    out['04-flujo.svg'] = s.finish()

    s = Scene('Dos evaluaciones, una mejora concreta', 'ARA revisa la interacción con agentes; MODA la madurez de la aplicación. Los hallazgos se conectan con el dolor, una mejora y su comprobación.')
    s.text(40,55,'D–I · EVALUAR PARA DECIDIR QUÉ CAMBIAR',18,750,'#387363')
    s.note(70,110,470,'ARA · INTERACCIÓN CON AGENTES','¿La aplicación permite actuar con controles claros?','workflow',165)
    s.note(660,110,470,'MODA · MODERNIZACIÓN','¿Qué capacidades de la aplicación conviene mejorar?','actor',165)
    s.arrow('M305 290V333H150V375'); s.arrow('M895 290V333H325')
    for x,label,title,kind in [(50,'PRIORIZAR','Vincular el hallazgo al dolor','pain'),(350,'CAMBIAR','Implementar una mejora','decision'),(650,'COMPROBAR','Probar el flujo completo','data'),(950,'COMPARAR','Reevaluar el mismo alcance','workflow')]:
        s.note(x,390,200,label,title,kind,160)
        if x<950:s.arrow(f'M{x+210} 470h75')
    s.text(600,610,'La evaluación técnica orienta cambios; el impacto se mide en el proceso.',22,650,anchor='middle')
    out['05-evaluar.svg'] = s.finish()

    s = Scene('Llevar el aprendizaje a AI-DLC', 'Inception acuerda problema, valor y alcance. Construction implementa y prueba una unidad. Operations mide el resultado y alimenta el siguiente ciclo.')
    s.text(40,55,'J · DEL DESCUBRIMIENTO A UNA MEJORA QUE SE MIDE',18,750,'#387363')
    for x,label,title,kind in [(55,'INCEPTION','Entender y acordar','decision'),(445,'CONSTRUCTION','Construir y comprobar','workflow'),(835,'OPERATIONS','Medir y aprender','data')]:
        s.note(x,135,310,label,title,kind,150)
    s.arrow('M380 210h45');s.arrow('M770 210h45')
    for x,lines in [(75,['Dolor y línea base','Oportunidad y autonomía','ARA/MODA y unidad']),(465,['Código y controles','Pruebas del flujo','Revisión con el equipo']),(855,['Tiempo de conciliación','Casos sin duplicados','Responsable y seguimiento'])]:
        for i,line in enumerate(lines): s.text(x,350+i*45,line,21,550)
    s.arrow('M990 475V545H210V480')
    s.text(600,600,'Ficha de valor: problema + indicador + meta + responsable.',24,650,anchor='middle')
    out['06-ai-dlc.svg'] = s.finish()
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args=parser.parse_args()
    for name, content in render().items():
        path=DEST/name
        if args.check:
            if not path.exists() or path.read_text()!=content:
                raise SystemExit(f'Ilustración desactualizada: {path.relative_to(ROOT)}')
        else:
            DEST.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
    print('6 ilustraciones de presentación sincronizadas.')


if __name__ == '__main__': main()
