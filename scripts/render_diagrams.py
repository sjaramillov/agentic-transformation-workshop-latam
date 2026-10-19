#!/usr/bin/env python3
"""Render portable SVG teaching boards; A–C share the discovery's source data."""
import argparse
import html
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
PALETTE = {'actor':'#e5dcf1','command':'#d7eaf2','data':'#dcebdc','event':'#ffe1bc','policy':'#fff0bb','pain':'#f9d8d0','decision':'#fff0bb','opportunity':'#fff0bb','workflow':'#d7eaf2','value':'#dcebdc','handoff':'#e5dcf1'}
LABELS = {'actor':'PERSONA','command':'COMANDO','data':'DATOS','event':'EVENTO','policy':'REGLA','pain':'DOLOR','decision':'DECISIÓN','opportunity':'OPORTUNIDAD','workflow':'FLUJO','value':'VALOR','handoff':'EVALUACIÓN'}


def esc(value):
    return html.escape(str(value), quote=True)


def lines(value, width, size):
    return textwrap.wrap(value, max(10, int(width / (size * .57))), break_long_words=False, break_on_hyphens=False) or ['']


class Board:
    def __init__(self, width, title, subtitle, kicker):
        self.width = width
        self.parts = []
        self.title = title
        self.subtitle = subtitle
        self.text(40, 42, kicker, 15, 750, '#276459')
        self.text(40, 94, title, 38, 760)
        self.text(40, 129, subtitle, 19, 400, '#53645b')
        self.line(40, 155, width-40, 155, '#cbd1c7')

    def rect(self,x,y,w,h,fill,stroke='none',radius=6,extra=''):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>')

    def text(self,x,y,value,size=18,weight=400,color='#203b33',anchor='start'):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{esc(value)}</text>')

    def paragraph(self,x,y,value,width,size=18,weight=400,color='#203b33'):
        for line in lines(value,width,size):
            self.text(x,y,line,size,weight,color)
            y += size*1.35
        return y

    def line(self,x1,y1,x2,y2,color='#a3afa4',dashed=False,arrow=False):
        extra = ('stroke-dasharray="6 6" ' if dashed else '') + ('marker-end="url(#arrow)"' if arrow else '')
        self.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="2" {extra}/>')

    @staticmethod
    def note_height(item,w):
        return 54 + len(lines(item['title'],w-32,20))*27 + len(lines(item['text'],w-32,17))*23 + (28 if item.get('badge') else 0)

    def note(self,x,y,w,item,height=None):
        h = height or self.note_height(item,w)
        fill = PALETTE[item.get('kind','decision')]
        selected = bool(item.get('selected_after'))
        self.rect(x+2,y+4,w,h,'#273f3112')
        self.rect(x,y,w,h,fill,'#276459' if selected else '#203b3314',4, 'stroke-width="3"' if selected else '')
        self.parts.append(f'<path d="M{x+w-18} {y}h18v18z" fill="#203b3315"/>')
        label = item.get('label', LABELS[item.get('kind','decision')]) + (' · '+item['after'].upper() if item.get('after') else '')
        if item.get('human_after'): label += ' · H'
        self.text(x+16,y+25,label,12,800)
        end = self.paragraph(x+16,y+53,item['title'],w-32,20,750)
        end = self.paragraph(x+16,end+3,item['text'],w-32,17)
        if item.get('badge'):
            self.paragraph(x+16,end+7,item['badge'],w-32,14,750,'#276459')
        return h

    def strip(self,y,title,body):
        self.text(40,y,title,15,800,'#276459')
        return self.paragraph(40,y+29,body,self.width-80,18)+24

    def finish(self,y,source):
        self.line(40,y,self.width-40,y,'#cbd1c7')
        self.text(40,y+30,source,14,400,'#53645b')
        self.text(self.width-40,y+30,'BOOKING MIT · MATERIAL ABIERTO',13,700,'#53645b','end')
        height = y+55
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{esc(self.title)}</title><desc id="desc">{esc(self.subtitle)}</desc>
<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".8" fill="#c4cbbd"/></pattern><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#276459"/></marker></defs>
<rect width="100%" height="100%" fill="#f6f4ed"/><rect width="100%" height="100%" fill="url(#dots)" opacity=".55"/>
<g font-family="system-ui,-apple-system,Segoe UI,sans-serif">\n'''+'\n'.join(self.parts)+'</g>\n</svg>\n'


def support(board,y,items):
    gap=18
    w=(board.width-80-gap*(len(items)-1))/len(items)
    h=max(board.note_height(item,w) for item in items)
    for i,item in enumerate(items): board.note(40+i*(w+gap),y,w,item,h)
    return y+h+30


def grid(data,phase):
    w=248 if phase=='A' else 215
    left=190
    width=left+len(data['columns'])*(w+16)+24
    b=Board(width,'Entender dónde duele el proceso' if phase=='A' else 'Proponer, aprobar, ejecutar y recuperar',
        'Las notas se alinean con el momento del proceso al que pertenecen.' if phase=='A' else 'Cada columna es un paso; cada carril muestra quién actúa y qué información necesita.',
        f'{phase} · '+('DISCOVERY CON EL CLIENTE' if phase=='A' else 'DISEÑO DEL FLUJO'))
    y=b.strip(190,'EMPIEZA CON EL DOLOR' if phase=='A' else 'UNIDAD DEL EJERCICIO',
        '«Se perdió la respuesta. ¿La reserva quedó creada y el cobro se realizó?» Primero escucha; después ubica la excepción.' if phase=='A' else 'Crear una reserva aprobada → consultar → cancelar con una aprobación nueva. Rechazar termina sin escritura.')
    for c,col in enumerate(data['columns']):
        x=left+c*(w+16)
        b.paragraph(x+10,y,col['label'],w-10,17,750)
        if c < len(data['columns'])-1: b.line(x+w,y-6,x+w+12,y-6,'#276459',arrow=True)
    y+=60
    for row in data['rows']:
        stacks=[[i for i in data['items'] if i['row']==row['id'] and i['column']==col['id']] for col in data['columns']]
        rh=max([sum(b.note_height(i,w)+12 for i in items) for items in stacks]+[85])+20
        b.rect(24,y-10,width-48,rh,'#fffdf580','#d2d8cd')
        b.paragraph(40,y+28,row['label'],135,19,750)
        for c,items in enumerate(stacks):
            x=left+c*(w+16)
            py=y
            for item in items:
                py += b.note(x,py,w,item)+12
            if not items: b.text(x+w/2,y+35,'·',24,400,'#869789','middle')
        if phase=='A': b.line(left+4*(w+16)-8,y-10,left+4*(w+16)-8,y+rh-10,'#b67c6b',dashed=True)
        if phase=='C':
            b.line(left+3*(w+16)-8,y-10,left+3*(w+16)-8,y+rh-10,'#9d8124',dashed=True)
            b.line(left+4*(w+16)-8,y-10,left+4*(w+16)-8,y+rh-10,'#9d8124',dashed=True)
        y+=rh+12
    if phase=='C':
        y=b.strip(y+15,'SUPERFICIE PARA ARA','GET /bookings · GET /bookings/{id}: consultar. POST /bookings: crear. DELETE /bookings/{id}: cancelar.')
    y=support(b,y+12,data['support'])
    y=b.strip(y,'ASÍ SE FORMA EL TABLERO',
        'A1 dolor en bandeja → A2 límites → A3 eventos → A4 excepción → A5 personas y comandos → A6 reglas → A7 información → A8 prioridades → A9 dependencias.' if phase=='A' else 'C1 unidad → C2 intención y datos → C3 APIs → C4 propuesta, aprobación y ejecución → C5 recuperación → C6 contexto para ARA/MODA.')
    return b.finish(y,'Fuente editable: workshop/discovery.json · Estado final de la práctica')


def quadrant(data):
    b=Board(1480,'Elegir una oportunidad con criterio','Compara reglas, interpretación y datos disponibles; acuerda autonomía para cada acción.','B · OPORTUNIDAD Y AUTONOMÍA')
    y=b.strip(190,'CANDIDATAS → DATOS → CUADRANTES → VALOR → H → AUTONOMÍA','B1–B2 reúne notas en la bandeja; B3 las ubica; B4 compara valor; B5 marca intervención humana; B6 elige el alcance.')
    left=190; colw=420; gap=20; legendx=1090
    for c,col in enumerate(data['columns']): b.text(left+c*(colw+gap),y,col['label'],21,750)
    y+=25
    top=y
    for row in data['rows']:
        stacks=[[i for i in data['items'] if i['row']==row['id'] and i['column']==col['id']] for col in data['columns']]
        rh=max([sum(b.note_height(i,colw-40)+15 for i in items) for items in stacks]+[160])+68
        b.paragraph(40,y+48,row['label'],130,19,750)
        for c,items in enumerate(stacks):
            x=left+c*(colw+gap)
            b.rect(x,y,colw,rh,'#fffdf5','#c8d2c4')
            zone=next(z for z in data['zones'] if z['row']==row['id'] and z['column']==data['columns'][c]['id'])
            b.paragraph(x+20,y+27,zone['label'],colw-40,15,750,'#53645b')
            py=y+60
            for item in items: py+=b.note(x+20,py,colw-40,item)+15
            if not items: b.paragraph(x+22,py+28,'Sin candidata en este caso.',colw-45,18,400,'#53645b')
        y+=rh+20
    b.text(legendx,top+25,'PATRONES DE AUTONOMÍA',15,800,'#276459')
    ly=top+50
    for label,title,body,kind in [('A','Autonomía completa','El agente decide y actúa dentro del alcance acordado.','data'),('P','Decisión preparada','El agente propone; una persona decide. Elegido para crear y cancelar.','decision'),('E','Exploración asistida','El agente ayuda a comprender y explorar información.','workflow'),('G','Agente como control','Revisa o contrasta acciones frente a reglas.','actor')]:
        item={'kind':kind,'label':'PATRÓN','title':label+' · '+title,'text':body}
        ly+=b.note(legendx,ly,350,item)+16
    ly=b.paragraph(legendx,ly+15,'H · Intervención humana obligatoria. Los patrones se eligen por acción; no forman una escala.',350,18,650)
    y=max(y,ly)+25
    y=support(b,y,[data['support'][1],data['support'][2]])
    return b.finish(y,'Fuente editable: workshop/discovery.json · Posiciones cualitativas del caso')


def cycle():
    b=Board(1480,'Del hallazgo a una mejora comprobada','El proceso define qué importa. La evaluación aporta evidencia sobre las aplicaciones.','D–I · ARA Y MODA')
    y=b.strip(190,'ENTRADA: TABLEROS A–C','Dolor, tarea, autonomía, APIs, dependencias, commit y alcance. El mismo contexto acompaña la comparación.')
    y=support(b,y,[{'kind':'pain','label':'EVALUACIÓN ARA','title':'ARA · Interacción con agentes','text':'Revisa interfaces, identidad, datos, resiliencia y observabilidad. Distingue BLOCKER de RISK-SAFETY; ambos pueden aparecer como High.'},{'kind':'workflow','label':'EVALUACIÓN MODA','title':'MODA · Modernización','text':'Revisa infraestructura, arquitectura, datos, seguridad y operación. Comprueba aplicabilidad, puntuaciones y condiciones de cada ruta.'}])
    items=[{'kind':'decision','label':'PRIORIDAD','title':'1 · Priorizar','text':'Conecta dolor → hallazgo → capacidad que falta. Define dueño y criterio de aceptación.'},{'kind':'data','label':'CAMBIO','title':'2 · Cambiar','text':'Implementa una unidad acotada. Una remediación asistida entrega un cambio para revisar.'},{'kind':'actor','label':'PRUEBA Y REVISIÓN','title':'3 · Comprobar','text':'Revisa el diff y prueba la operación, los fallos y la recuperación. Integra el cambio aceptado.'},{'kind':'event','label':'EVALUACIÓN','title':'4 · Reevaluar','text':'Evalúa el nuevo commit. Compara las mismas preguntas y explica cobertura, rúbrica y cambios.'}]
    y=support(b,y+32,items)
    b.line(1250,y-8,250,y-8,'#276459',dashed=True,arrow=True)
    b.text(740,y+20,'La comparación vuelve a alimentar las prioridades',18,650,'#276459','middle')
    y=support(b,y+58,[{'kind':'data','label':'TRAZABILIDAD','title':'Identidad y alcance','text':'Aplicación + tipo de análisis + question_id. Conserva commits, archivos y contextos de cada evaluación.'},{'kind':'decision','label':'INTERPRETACIÓN','title':'Lectura de MODA','text':'Cada categoría evaluada pesa igual. Si cambia la cobertura, revisa también las preguntas comunes.'},{'kind':'value','label':'MEDICIÓN','title':'Resultado del negocio','text':'Las pruebas comprueban comportamiento. El efecto sobre tiempo, errores y costo se mide con usuarios.'}])
    return b.finish(y,'Fuentes: guía del workshop y rúbricas de AWS Samples enlazadas en RECURSOS.md')


def operations():
    b=Board(1480,'Acordar quién sostiene cada mejora','Responsabilidades y decisiones para llevar una unidad probada a la operación.','J · MODELO OPERATIVO')
    data=[('Producto','Dolor y resultado','Acordar línea base, objetivo, alcance del piloto y decisión de continuar, ajustar o detener.','Métrica y responsable','value'),('Aplicación','Contrato y código','Mantener APIs, persistencia e idempotencia. Revisar el cambio y sus pruebas de aceptación.','Cambio revisado y probado','workflow'),('Seguridad','Identidad y aprobación','Definir quién puede consultar o escribir, qué aprueba y cómo se conserva la atribución.','Permisos y control por acción','actor'),('Plataforma','Entorno viable','Acordar runtime, secretos, despliegue y dependencias según las necesidades del servicio.','Destino y recuperación','data'),('Operación','Servicio sostenible','Preparar alertas, restauración, runbook y responsable de incidentes. Medir el resultado del piloto.','Señales y respuesta','pain')]
    y=190; xs=[40,225,510,1190]; widths=[165,265,660,250]
    for x,label in zip(xs,['RESPONSABLE','DECISIÓN','TRABAJO','ENTREGABLE']): b.text(x,y,label,14,800,'#276459')
    y+=24
    for owner,title,body,result,kind in data:
        h=150
        b.rect(30,y,1420,h,'#fffdf5','#d0d7cb')
        b.paragraph(xs[0]+10,y+38,owner,widths[0]-20,20,750)
        b.note(xs[1],y+12,widths[1],{'kind':kind,'label':'ACUERDO','title':title,'text':''},h-24)
        b.paragraph(xs[2]+15,y+40,body,widths[2]-35,21)
        b.paragraph(xs[3],y+40,result,widths[3]-10,20,650)
        y+=h+14
    y=b.strip(y+20,'CUANDO SE REUTILICE UNA TRANSFORMATION DEFINITION (TD)','Versiona su alcance y reglas; pruébala en repositorios representativos; revisa sus cambios y prepara reversión antes de ampliar su uso.')
    return b.finish(y,'Adaptar los responsables al equipo · AI_DLC.md y AGENTE_EJECUTABLE.md')


def value():
    b=Board(1200,'Del dolor a una mejora con valor','Preguntas y entregables para conectar discovery, ARA/MODA y AI-DLC.','RECORRIDO COMPLETO · BOOKING MIT')
    rows=[('INCEPTION · ENTENDER Y DECIDIR',[('pain','1 · ¿Dónde se atasca?','Cliente y coach: proceso, excepción y trabajo manual. Tablero A.'),('value','2 · ¿Qué cambiaría?','Línea base, resultado esperado, costo y alternativa. Tablero B y ficha de valor.')]),('INCEPTION · DELIMITAR Y EVALUAR',[('decision','3 · ¿Qué puede hacer?','Tarea, lecturas, escrituras y aprobación por acción. Tablero C.'),('workflow','4 · ¿Qué falta?','ARA: controles de interacción. MODA: brechas y alternativas de modernización.')]),('CONSTRUCTION → OPERATIONS',[('actor','5 · ¿Qué probamos?','Una unidad: agente, API y PostgreSQL. Pruebas de fallos, recuperación y reevaluación.'),('data','6 · ¿Qué resultado tuvo?','Medir tiempo humano, errores y costo. Continuar, ajustar o detener con el dueño.')])]
    y=200
    for label,items in rows:
        b.text(40,y,label,16,800,'#276459'); y+=28
        y=support(b,y,[{'kind':k,'label':{'pain':'PROBLEMA','value':'HIPÓTESIS','decision':'ALCANCE','workflow':'EVALUACIÓN','actor':'CONSTRUCTION','data':'OPERATIONS'}[k],'title':t,'text':body} for k,t,body in items])
        b.line(600,y-15,600,y+12,'#276459',arrow=True)
        y+=35
    y=b.strip(y,'EL CICLO CONTINÚA','La evaluación informa las decisiones iniciales y se repite después del cambio. El resultado medido alimenta el siguiente ciclo de AI-DLC.')
    return b.finish(y,'Caso práctico: FICHA_VALOR.md · AI_DLC.md · GUIA_REPLICACION.md')


def render():
    data=json.loads((ROOT/'workshop/discovery.json').read_text())['boards']
    return {'01-eventstorming.svg':grid(data['A'],'A'),'02-oportunidad-agente.svg':quadrant(data['B']),'03-workflow-rebooking.svg':grid(data['C'],'C'),'04-ciclo-ara-moda.svg':cycle(),'05-modelo-operativo.svg':operations(),'06-valor-ai-dlc.svg':value()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Check that committed SVGs match their source.')
    args=parser.parse_args()
    stale=[]
    for name,svg in render().items():
        path=ROOT/'diagramas'/name
        if args.check:
            if not path.exists() or path.read_text()!=svg: stale.append(name)
        else: path.write_text(svg)
    if stale: parser.exit(1,'Regenera los diagramas: '+', '.join(stale)+'\n')
    print('Six diagrams '+('match their source.' if args.check else 'rendered.'))


if __name__=='__main__': main()
