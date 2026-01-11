import markdown2, re

from collections import defaultdict

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_user, logout_user, current_user, login_required, logout_user

from jinja2 import Template

from sqlalchemy import or_

from werkzeug.utils import secure_filename
from io import BytesIO

from audithunter import db, login_manager

from audithunter.models import Missions, MissionDroits, Domaines, Themes, Chapitres, Questions, QuestionsCache, MissionReponse, RecommandationsAudit
from audithunter.forms import MissionForm, QuestionnaireForm
from audithunter.utils import log_action, check_permissions

from sqlalchemy import or_

import datetime, os, tempfile, subprocess, yaml

compil = Blueprint('compil', __name__)
current_dir = os.path.dirname(os.path.abspath(__file__))


#region Convention
@compil.route('/gen_docx_convention/<int:id_mission>', methods=['GET'])
@log_action
@login_required
@check_permissions(lambda id_mission: id_mission, required_roles=['chef de projet', 'auditeur'])
def gen_docx_convention(id_mission):
    with open(current_dir+'/../templates/latex/template_convention.tex') as file:
        template_content = file.read()
    variables = get_mission_data_as_yaml(id_mission)
    template = Template(template_content)
    output_content = template.render(variables)

    tmp_convention_tex = tempfile.NamedTemporaryFile(delete=False, suffix='.tex')
    tmp_convention_docx = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')

    fichier = open(tmp_convention_tex.name, "w")
    fichier.write(output_content)
    fichier.close()

    #try:
    #    subprocess.run(['pandoc', tmp_convention_tex.name, '-o', tmp_convention_docx.name], check=True)
    #except:
    #    return render_template('erreur.html', erreur="Erreur de compilation avec Pandoc")

    try:
        subprocess.run(
            ['pandoc', tmp_convention_tex.name, '-o', tmp_convention_docx.name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except subprocess.CalledProcessError as e:
        erreur = (
            f"Code retour : {e.returncode}\n\n"
            f"STDOUT :\n{e.stdout}\n\n"
            f"STDERR :\n{e.stderr}"
        )
        return render_template('erreur.html', erreur=erreur)    

    try:
        with open(tmp_convention_docx.name, 'rb') as output_file:
            buffer = BytesIO(output_file.read())
        buffer.seek(0)
        flash('Report generated successfully', 'success')
        return send_file(buffer, as_attachment=True, download_name=f'convention_{id_mission}_{datetime.datetime.today()}.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except:
        return render_template('erreur.html', erreur="Erreur lors de la génération du rapport")
    finally:
        if os.path.exists(tmp_convention_tex.name):
            os.remove(tmp_convention_tex.name)
        if os.path.exists(tmp_convention_docx.name):
            os.remove(tmp_convention_docx.name)


#region Contrat
@compil.route('/gen_docx_contrat/<int:id_mission>', methods=['GET'])
@log_action
@login_required
@check_permissions(lambda id_mission: id_mission, required_roles=['chef de projet', 'auditeur'])
def gen_docx_contrat(id_mission):
    with open(current_dir+'/../templates/latex/template_contrat.tex') as file:
        template_content = file.read()
    variables = get_mission_data_as_yaml(id_mission)
    template = Template(template_content)
    output_content = template.render(variables)

    tmp_contrat_tex = tempfile.NamedTemporaryFile(delete=False, suffix='.tex')
    tmp_contrat_docx = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')

    fichier = open(tmp_contrat_tex.name, "w")
    fichier.write(output_content)
    fichier.close()

    try:
        subprocess.run(['pandoc', tmp_contrat_tex.name, '-o', tmp_contrat_docx.name], check=True)
    except:
        return render_template('erreur.html', erreur="Erreur lors de la génération du rapport")

    try:
        with open(tmp_contrat_docx.name, 'rb') as output_file:
            buffer = BytesIO(output_file.read())
        buffer.seek(0)
        flash('Report generated successfully', 'success')
        return send_file(buffer, as_attachment=True, download_name=f'contrat_{id_mission}_{datetime.datetime.today()}.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except:
        return render_template('erreur.html', erreur="Erreur lors de la génération du rapport")
    finally:
        if os.path.exists(tmp_contrat_tex.name):
            os.remove(tmp_contrat_tex.name)
        if os.path.exists(tmp_contrat_docx.name):
            os.remove(tmp_contrat_docx.name)

#region Rapport
@compil.route('/gen_docx_rapport/<int:id_mission>', methods=['GET']) # redondant peut être éditer ça
@log_action
@login_required
@check_permissions(lambda id_mission: id_mission, required_roles=['chef de projet', 'auditeur'])
def gen_docx_rapport(id_mission):
    with open(current_dir+'/../templates/latex/template_rapport.tex') as file:
        template_content = file.read()
    content_rapport = gen_docx_content_rapport(id_mission)
    template = Template(template_content)
    output_content = template.render(content_rapport)

    tmp_rapport_tex = tempfile.NamedTemporaryFile(delete=False, suffix='.tex')
    tmp_rapport_docx = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')

    fichier = open(tmp_rapport_tex.name, "w")
    fichier.write(output_content)
    fichier.close()
    try:
        print(['pandoc', tmp_rapport_tex.name, '-o', tmp_rapport_docx.name])
    
        subprocess.run(['pandoc', tmp_rapport_tex.name, '-o', tmp_rapport_docx.name],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    except subprocess.CalledProcessError as e:
        print(
            f"Code retour : {e.returncode}\n\n"
            f"STDOUT :\n{e.stdout}\n\n"
            f"STDERR :\n{e.stderr}"
        )
        return render_template('erreur.html', erreur="Erreur lors de la génération du rapport")

    try:
        with open(tmp_rapport_docx.name, 'rb') as output_file:
            buffer = BytesIO(output_file.read())
        buffer.seek(0)
        flash('Report generated successfully', 'success')
        return send_file(buffer, as_attachment=True, download_name=f'rapport_{id_mission}_{datetime.datetime.today()}.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except:
        return render_template('erreur.html', erreur="Erreur lors de la génération du rapport")
    finally:
        if os.path.exists(tmp_rapport_tex.name):
            os.remove(tmp_rapport_tex.name)
        if os.path.exists(tmp_rapport_docx.name):
            os.remove(tmp_rapport_docx.name)

@compil.route('/gen_tex_rapport/<int:id_mission>', methods=['GET']) # redondant peut être éditer ça
@log_action
@login_required
@check_permissions(lambda id_mission: id_mission, required_roles=['chef de projet', 'auditeur'])
def gen_tex_rapport(id_mission):
    with open(current_dir+'/../templates/latex/template_rapport.tex') as file:
        template_content = file.read()
    content_rapport = gen_docx_content_rapport(id_mission)
    template = Template(template_content)
    output_content = template.render(content_rapport)

    tmp_rapport_tex = tempfile.NamedTemporaryFile(delete=False, suffix='.tex')

    fichier = open(tmp_rapport_tex.name, "w")
    fichier.write(output_content)
    fichier.close()

    try:
        with open(tmp_rapport_tex.name, 'rb') as output_file:
            buffer = BytesIO(output_file.read())
        buffer.seek(0)
        flash('Report generated successfully', 'success')
        return send_file(buffer, as_attachment=True, download_name=f'rapport_{id_mission}_{datetime.datetime.today()}.tex', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except:
        return render_template('erreur.html', erreur="Erreur lors de la génération du rapport")
    finally:
        if os.path.exists(tmp_rapport_tex.name):
            os.remove(tmp_rapport_tex.name)


#region FONCTIONS ANNEXES

def get_mission_data_as_yaml(id_mission):
    mission = db.session.query(Missions).filter_by(id_mission=id_mission).first()
    if not mission:
        return None
    mission_data = {
        'mission': mission.mission,
        'clientname': mission.client_name,
        'clientcompany': mission.client_company,
        'clientaddress': mission.client_address,
        'clientsiren': mission.client_siren,
        'clientproduit': mission.client_produit,
        'clientrepresentative': mission.client_representative,
        'clienttitle': mission.client_title,
        'auditorname': "David Perez",
        'auditorcompany': "byDacodhack",
        'auditoraddress': "42 rue de l'aiguillerie, 34000 Montpellier",
        'auditorsiren': "922793989",
        'auditorrepresentative': "David Perez",
        'auditortitle': "Auditeur",
        'AUDITORLOGO': './../audithunter/audithunter/templates/logo/logo.png', # Attention au chemin pour avoir le logo
        'VERSIONDOCUMENT': "v-1.0",
        'DATEDOCUMENT': datetime.datetime.today()
        }
    return mission_data


def gen_docx_content_rapport(id_mission):
    domaines = {}

    mission = Missions.query.get(id_mission)
    reponses = MissionReponse.query.filter_by(id_mission=id_mission).all()

    for rep in reponses:
        domaine = rep.questions.chapitres.domaines
        chapitre = rep.questions.chapitres

        # Domaine
        if domaine.id_domaine not in domaines:
            domaines[domaine.id_domaine] = {
                "id_domaine": domaine.id_domaine,
                "domaine": domaine.domaine,
                "chapitres": {}
            }

        # Chapitre
        if chapitre.id_chapitre not in domaines[domaine.id_domaine]["chapitres"]:
            domaines[domaine.id_domaine]["chapitres"][chapitre.id_chapitre] = {
                "id_chapitre": chapitre.id_chapitre,
                "chapitre": chapitre.chapitre,
                "questions": []
            }

        # Question / Réponse
        domaines[domaine.id_domaine]["chapitres"][chapitre.id_chapitre]["questions"].append({
            "question": rep.questions.question,
            "objectif": rep.questions.objectif,
            "reponse": rep.reponse,
            "evaluation": rep.evaluation,
            "piece_jointe": rep.piece_jointe
        })

    # Conversion dict → listes (important pour Jinja)
    report_data = {
        "mission": mission.to_dict(),
        "domaines": [
            {
                **d,
                "chapitres": list(d["chapitres"].values())
            }
            for d in domaines.values()
        ]
    }

    print(report_data)
    return report_data #rapport_latex


    
