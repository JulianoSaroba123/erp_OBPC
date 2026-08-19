from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensoes import db
from app.membros.membros_model import Membro
from app.obreiros.obreiros_model import Obreiro
from app.secretaria.atas.atas_model import Ata
from app.secretaria.oficios.oficios_model import Oficio
from app.secretaria.inventario.inventario_model import ItemInventario
from app.secretaria.participacao.participacao_model import ParticipacaoObreiro
from app.midia.midia_model import Certificado, CarteiraMembro


secretaria_bp = Blueprint("secretaria", __name__, template_folder="templates")


@secretaria_bp.route("/secretaria/visao-geral")
@login_required
def visao_geral():
    if hasattr(current_user, "tem_acesso_secretaria") and not current_user.tem_acesso_secretaria():
        abort(403)

    kpis = {
        "membros_total": db.session.query(func.count(Membro.id)).scalar() or 0,
        "membros_ativos": db.session.query(func.count(Membro.id)).filter(Membro.status == "Ativo").scalar() or 0,
        "liderancas": db.session.query(func.count(Membro.id)).filter(Membro.tipo == "Lider").scalar() or 0,
        "obreiros": db.session.query(func.count(Obreiro.id)).scalar() or 0,
        "carteiras": db.session.query(func.count(CarteiraMembro.id)).filter(CarteiraMembro.ativo.is_(True)).scalar() or 0,
        "certificados": db.session.query(func.count(Certificado.id)).scalar() or 0,
    }

    indicadores = {
        "atas": db.session.query(func.count(Ata.id)).scalar() or 0,
        "oficios": db.session.query(func.count(Oficio.id)).scalar() or 0,
        "inventario": db.session.query(func.count(ItemInventario.id)).scalar() or 0,
        "participacoes": db.session.query(func.count(ParticipacaoObreiro.id)).scalar() or 0,
    }

    pendencias = []
    membros_sem_contato = (
        db.session.query(func.count(Membro.id))
        .filter((Membro.telefone.is_(None) | (Membro.telefone == "")) | (Membro.email.is_(None) | (Membro.email == "")))
        .scalar()
        or 0
    )
    if membros_sem_contato > 0:
        pendencias.append({
            "tipo": "warning",
            "titulo": "Membros sem contato completo",
            "descricao": f"{membros_sem_contato} cadastro(s) sem telefone ou e-mail.",
        })

    membros_inativos = db.session.query(func.count(Membro.id)).filter(Membro.status == "Inativo").scalar() or 0
    if membros_inativos > 0:
        pendencias.append({
            "tipo": "info",
            "titulo": "Cadastros inativos",
            "descricao": f"{membros_inativos} membro(s) marcados como inativos.",
        })

    itens_inativos = db.session.query(func.count(ItemInventario.id)).filter(ItemInventario.ativo.is_(False)).scalar() or 0
    if itens_inativos > 0:
        pendencias.append({
            "tipo": "warning",
            "titulo": "Itens patrimoniais inativos",
            "descricao": f"{itens_inativos} item(ns) com status inativo no inventário.",
        })

    oficios_cancelados = db.session.query(func.count(Oficio.id)).filter(Oficio.status == "Cancelado").scalar() or 0
    if oficios_cancelados > 0:
        pendencias.append({
            "tipo": "danger",
            "titulo": "Ofícios cancelados",
            "descricao": f"{oficios_cancelados} ofício(s) com status Cancelado.",
        })

    atividade = {
        "membros": Membro.query.order_by(Membro.data_cadastro.desc()).limit(5).all(),
        "atas": Ata.query.order_by(Ata.criado_em.desc()).limit(5).all(),
        "oficios": Oficio.query.order_by(Oficio.criado_em.desc()).limit(5).all(),
        "certificados": Certificado.query.order_by(Certificado.data_criacao.desc()).limit(5).all(),
        "carteiras": CarteiraMembro.query.order_by(CarteiraMembro.data_criacao.desc()).limit(5).all(),
        "inventario": ItemInventario.query.order_by(ItemInventario.criado_em.desc()).limit(5).all(),
    }

    return render_template(
        "secretaria/visao_geral.html",
        kpis=kpis,
        indicadores=indicadores,
        pendencias=pendencias,
        atividade=atividade,
    )
