"""Generate reviewable MySQL DDL and explicit ORM mappings from the design catalog.

Run only when changing the schema; this is not executed by the web application.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'database/schema_catalog.json').read_text())
CLASSES = dict(zip([t['name'] for t in CATALOG], [
    'User','Doctor','Patient','MedicalCase','Visit','Symptom','CaseSymptom',
    'MedicalHistory','Allergy','LifestyleHistory','VitalSign','Examination',
    'Diagnosis','Medicine','Prescription','PrescriptionMedicine','Appointment',
    'FollowUp','AuditLog','MonthlyCaseStatistic']))
MODULES = dict(zip(CLASSES, ['user','doctor','patient','case','visit','symptom',
    'case','patient','patient','patient','visit','visit','diagnosis','medicine',
    'prescription','prescription','appointment','followup','audit','report']))
INDEXES = {
    'patients': [('last_name','first_name','patient_id'),('first_name','patient_id'),('phone',),('created_at','patient_id')],
    'doctors': [('last_name','first_name','doctor_id')],
    'medical_cases': [('patient_id','case_date','case_id'),('doctor_id','record_state','case_status','case_date','case_id'),('record_state','case_status','case_date','case_id'),('case_date','case_id')],
    'visits': [('case_id','visit_date','visit_id'),('doctor_id','visit_date','visit_id'),('visit_date','visit_id')],
    'case_symptoms': [('symptom_id','case_id')],
    'medical_history': [('patient_id','diagnosed_date','history_id')],
    'allergies': [('patient_id',)],
    'diagnoses': [('diagnosis_name','visit_id')],
    'medicines': [('medicine_name','medicine_id')],
    'prescriptions': [('doctor_id','prescription_date','prescription_id'),('prescription_date','prescription_id')],
    'prescription_medicines': [('medicine_id','prescription_id')],
    'appointments': [('doctor_id','appointment_date','start_time','appointment_id'),('patient_id','appointment_date','appointment_id'),('appointment_date','status','appointment_id')],
    'follow_ups': [('status','scheduled_date','follow_up_id'),('visit_id',)],
    'audit_logs': [('created_at','audit_id'),('user_id','created_at','audit_id'),('entity_type','entity_id','created_at','audit_id')],
}

def sa_type(value):
    base, *args = re.split(r'[(),]', value)
    args = ', '.join(a for a in args if a)
    name = {'INT':'Integer','BIGINT':'BigInteger','SMALLINT':'SmallInteger',
            'VARCHAR':'String','TEXT':'Text','DATE':'Date','TIME':'Time',
            'DATETIME':'DATETIME','DECIMAL':'Numeric','BOOLEAN':'Boolean'}[base]
    return name + (f'({"fsp=" if base == "DATETIME" else ""}{args})' if args else '')

def generate():
    sql = ['-- CareTrack: fictional data only. MySQL 8.0.31+ / InnoDB.', '-- Select the target database in your connection.', '']
    files = {}
    header = 'from sqlalchemy import Column, Integer, BigInteger, SmallInteger, String, Text, Date, Time, Numeric, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Index, text\nfrom sqlalchemy.dialects.mysql import DATETIME\nfrom app.database.base import Base\n\n'
    imports = []
    for t in CATALOG:
        name, cls, module = t['name'], CLASSES[t['name']], MODULES[t['name']]
        cols, orm = [], [f'class {cls}(Base):',f'    __tablename__ = {name!r}']
        for c in t['columns']:
            flags = c['flags']
            ddl = f"  `{c['name']}` {c['type']}" + (' NOT NULL' if 'NN' in flags else ' NULL')
            if c['default'] is not None: ddl += ' DEFAULT ' + c['default']
            if 'AI' in flags: ddl += ' AUTO_INCREMENT'
            cols.append(ddl)
            args = [sa_type(c['type'])]
            if c.get('target'): args.append(f"ForeignKey({c['target']!r}, ondelete={c['delete']!r}, onupdate='CASCADE')")
            if 'PK' in flags: args.append('primary_key=True')
            if 'AI' in flags: args.append('autoincrement=True')
            elif 'PK' in flags: args.append('autoincrement=False')
            args.append('nullable=' + str('NN' not in flags))
            if 'UQ' in flags: args.append('unique=True')
            if c['default'] is not None: args.append(f"server_default=text({c['default']!r})")
            orm.append(f"    {c['name']} = Column({', '.join(args)})")
        pk = [c['name'] for c in t['columns'] if 'PK' in c['flags']]
        cols.append('  PRIMARY KEY ('+', '.join('`'+x+'`' for x in pk)+')')
        constraints = []
        for c in t['columns']:
            if 'UQ' in c['flags']: cols.append(f"  CONSTRAINT uq_{name}_{c['name']} UNIQUE (`{c['name']}`)")
            if c.get('target'):
                parent, key = c['target'].split('.')
                cols.append(f"  CONSTRAINT fk_{name}_{c['name']} FOREIGN KEY (`{c['name']}`) REFERENCES `{parent}` (`{key}`) ON DELETE {c['delete']} ON UPDATE CASCADE")
        for i,g in enumerate(t.get('unique_groups', [])):
            cname = f'uq_{name}_group_{i}'
            cols.append(f"  CONSTRAINT {cname} UNIQUE ({', '.join(g)})")
            constraints.append(f"UniqueConstraint({', '.join(repr(x) for x in g)}, name={cname!r})")
        for i, check in enumerate(t['checks']):
            cname = f'ck_{name}_{i}'
            cols.append(f'  CONSTRAINT {cname} CHECK ({check})')
            constraints.append(f'CheckConstraint({check!r}, name={cname!r})')
        for i,fields in enumerate(INDEXES.get(name, [])):
            idx = f'ix_{name}_{i}'
            cols.append(f"  INDEX {idx} ({', '.join(fields)})")
            constraints.append(f"Index({idx!r}, {', '.join(repr(x) for x in fields)})")
        sql.extend([f'CREATE TABLE `{name}` (', ',\n'.join(cols), ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;', ''])
        orm.extend(['    __table_args__ = ('] + ['        '+s+',' for s in constraints] + ["        {'mysql_engine':'InnoDB', 'mysql_charset':'utf8mb4', 'mysql_collate':'utf8mb4_0900_ai_ci'},",'    )',''])
        files.setdefault(module, []).extend(orm)
        imports.append(f'from .{module} import {cls}')
    (ROOT/'database/01_create_database.sql').write_text('CREATE DATABASE IF NOT EXISTS caretrack CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;\n')
    (ROOT/'database/02_schema.sql').write_text('\n'.join(sql))
    for module, lines in files.items(): (ROOT/f'backend/app/models/{module}.py').write_text(header+'\n'.join(lines))
    (ROOT/'backend/app/models/__init__.py').write_text('\n'.join(imports)+'\n\nMODELS = {'+', '.join(f'{name!r}: {cls}' for name,cls in CLASSES.items())+'}\n')
    print(f'Generated DDL and mappings for {len(CATALOG)} tables.')

if __name__ == '__main__': generate()
