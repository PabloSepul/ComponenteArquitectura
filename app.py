from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gastos_comunes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo para Departamento y Gastos Comunes
class Departamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), nullable=False, unique=True)

class GastoComun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    departamento_id = db.Column(db.Integer, db.ForeignKey('departamento.id'), nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    año = db.Column(db.Integer, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    pagado = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.Date, nullable=True)

# Crear las tablas
with app.app_context():
    db.create_all()

# Generación de los gastos comunes
@app.route('/gastos_comunes/generar', methods=['POST'])
def generar_gastos_comunes():
    data = request.get_json()
    mes = data.get('mes')
    año = data.get('año')
    monto_base = data.get('monto_base', 50000)  # Monto base para cada departamento

    departamentos = Departamento.query.all()
    if not departamentos:
        return jsonify({'error': 'No hay departamentos registrados'}), 404

    gastos_generados = []
    for departamento in departamentos:
        if GastoComun.query.filter_by(departamento_id=departamento.id, mes=mes, año=año).first():
            continue  # Evitar duplicados
        gasto = GastoComun(departamento_id=departamento.id, mes=mes, año=año, monto=monto_base)
        db.session.add(gasto)
        gastos_generados.append({
            'departamento': departamento.numero,
            'mes': mes,
            'año': año,
            'monto': monto_base
        })

    db.session.commit()
    return jsonify({'message': 'Gastos generados', 'gastos': gastos_generados}), 201

# Marcar un gasto como pagado
@app.route('/gastos_comunes/pagar', methods=['POST'])
def marcar_como_pagado():
    data = request.get_json()
    departamento_num = data.get('departamento')
    mes = data.get('mes')
    año = data.get('año')
    fecha_pago = data.get('fecha_pago')

    departamento = Departamento.query.filter_by(numero=departamento_num).first()
    if not departamento:
        return jsonify({'error': 'Departamento no encontrado'}), 404

    gasto = GastoComun.query.filter_by(departamento_id=departamento.id, mes=mes, año=año).first()
    if not gasto:
        return jsonify({'error': 'Gasto común no encontrado'}), 404

    if gasto.pagado:
        return jsonify({'estado': 'Pago duplicado'}), 400

    gasto.pagado = True
    gasto.fecha_pago = datetime.strptime(fecha_pago, '%Y-%m-%d').date()

    # Comparar como objetos de tipo date
    estado = "Pago exitoso dentro del plazo" if date(gasto.año, gasto.mes, 1) >= gasto.fecha_pago else "Pago exitoso fuera de plazo"

    db.session.commit()
    return jsonify({
        'departamento': departamento.numero,
        'mes': mes,
        'año': año,
        'fecha_pago': gasto.fecha_pago.strftime('%Y-%m-%d'),
        'estado': estado
    }), 200


# Listado de gastos comunes pendientes de pago
@app.route('/gastos_comunes/pendientes', methods=['GET'])
def listar_gastos_pendientes():
    mes = int(request.args.get('mes'))
    año = int(request.args.get('año'))

    gastos_pendientes = GastoComun.query.filter(
        GastoComun.pagado == False,
        (GastoComun.año < año) | ((GastoComun.año == año) & (GastoComun.mes <= mes))
    ).order_by(GastoComun.año, GastoComun.mes).all()

    if not gastos_pendientes:
        return jsonify({'message': 'Sin montos pendientes'}), 200

    resultado = [{
        'departamento': Departamento.query.get(gasto.departamento_id).numero,
        'mes': gasto.mes,
        'año': gasto.año,
        'monto': gasto.monto
    } for gasto in gastos_pendientes]

    return jsonify(resultado), 200

# registrar departamentos
@app.route('/departamentos', methods=['POST'])
def registrar_departamento():
    data = request.get_json()
    numero = data.get('numero')

    if Departamento.query.filter_by(numero=numero).first():
        return jsonify({'error': 'El departamento ya existe'}), 400

    nuevo_departamento = Departamento(numero=numero)
    db.session.add(nuevo_departamento)
    db.session.commit()
    return jsonify({'message': 'Departamento registrado', 'numero': numero}), 201

if __name__ == '__main__':
    app.run(debug=True)


# #Recordatorio para Rocio y Pablo del futuro para agregar via postman 
# /departamentos { "numero": "123"} POST
# /gastos_comunes/generar { "mes": 2, "año": 2024, "monto_base": 50000} POST
# /gastos_comunes/pagar {"departamento": "1305","mes": 10,"año": 2024,"fecha_pago": "2024-11-03"} POST
# /gastos_comunes/pendientes?mes=10&año=2024 GET
# 
# 
# 
# 