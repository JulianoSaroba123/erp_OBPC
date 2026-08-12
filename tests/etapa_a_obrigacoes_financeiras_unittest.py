from datetime import date
from decimal import Decimal
import unittest
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.extensoes import db
from app import create_app
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.despesas_fixas_model import DespesaFixaConselho
from app.financeiro.projeto_model import Projeto
from app.financeiro.comprovante_model import Comprovante
from app.financeiro.financeiro_routes import (
    gerar_obrigacoes_despesas_fixas,
    _criar_obrigacao_despesa_fixa_sem_commit,
    _calcular_admin_sede_30_legado,
    _criar_obrigacao_admin_sede_sem_commit,
    gerar_obrigacao_admin_sede_30,
)
from app.financeiro.envios_sede_model import EnvioSede
from app.configuracoes.configuracoes_model import Configuracao
from app.financeiro.obrigacoes_model import (
    ObrigacaoFinanceira,
    ObrigacaoEvento,
    PagamentoObrigacao,
    PagamentoObrigacaoItem,
)


class TestEtapaAObrigacoesFinanceiras(unittest.TestCase):
    NOVAS_TABELAS = {
        "obrigacoes_financeiras",
        "pagamentos_obrigacao",
        "pagamentos_obrigacao_itens",
        "obrigacao_eventos",
    }

    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config["TESTING"] = True
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(cls.app)

        with cls.app.app_context():
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.session.rollback()

        # Limpeza determinística para isolamento dos cenários
        db.session.query(Comprovante).delete()
        db.session.query(PagamentoObrigacaoItem).delete()
        db.session.query(ObrigacaoEvento).delete()
        db.session.query(PagamentoObrigacao).delete()
        db.session.query(ObrigacaoFinanceira).delete()
        db.session.query(EnvioSede).delete()
        db.session.query(DespesaFixaConselho).delete()
        db.session.query(Lancamento).delete()
        db.session.query(Projeto).delete()
        db.session.query(Configuracao).delete()
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        db.session.remove()
        self.ctx.pop()

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _run_schema_script(self, database_url: str):
        env = os.environ.copy()
        env["DATABASE_URL"] = database_url
        env["PYTHONPATH"] = "."

        return subprocess.run(
            [
                sys.executable,
                "scripts/garantir_schema_obrigacoes_financeiras.py",
            ],
            cwd=str(self._project_root()),
            env=env,
            capture_output=True,
            text=True,
        )

    def _nova_obrigacao(self, valor="1000.00", **kwargs):
        obrigacao = ObrigacaoFinanceira(
            tipo_obrigacao=kwargs.get("tipo_obrigacao", "OUTRA"),
            origem_obrigacao=kwargs.get("origem_obrigacao", "manual"),
            referencia_origem_tipo=kwargs.get("referencia_origem_tipo"),
            referencia_origem_id=kwargs.get("referencia_origem_id"),
            categoria=kwargs.get("categoria", "TESTE"),
            descricao=kwargs.get("descricao", "Obrigação de teste"),
            competencia_mes=kwargs.get("competencia_mes", 7),
            competencia_ano=kwargs.get("competencia_ano", 2026),
            valor_devido=Decimal(valor),
            status=kwargs.get("status", "PENDENTE"),
        )
        obrigacao.validar()
        obrigacao.validar_duplicidade_automatica(db.session)
        db.session.add(obrigacao)
        db.session.flush()
        return obrigacao

    def _novo_pagamento(self, valor="1000.00", tipo_pagamento="PAGAMENTO_BANCARIO", lancamento_id=None):
        pagamento = PagamentoObrigacao(
            data_pagamento=date(2026, 7, 3),
            valor_pago=Decimal(valor),
            tipo_pagamento=tipo_pagamento,
            forma_pagamento="PIX",
            lancamento_financeiro_id=lancamento_id,
        )
        pagamento.validar()
        db.session.add(pagamento)
        db.session.flush()
        return pagamento

    def _nova_despesa_fixa(self, nome, valor=100.0, ativa=True, descricao="Despesa fixa teste", categoria="DESP. FIXAS"):
        despesa = DespesaFixaConselho(
            nome=nome,
            descricao=descricao,
            valor_padrao=valor,
            ativo=ativa,
            categoria=categoria,
        )
        db.session.add(despesa)
        db.session.flush()
        return despesa

    def _saldo_lancamentos(self):
        saldo = Decimal("0.00")
        for lancamento in Lancamento.query.all():
            valor = Decimal(str(lancamento.valor or 0))
            if (lancamento.tipo or "").strip().lower() == "entrada":
                saldo += valor
            else:
                saldo -= valor
        return saldo.quantize(Decimal("0.01"))

    def _total_saidas_lancamentos(self):
        total = Decimal("0.00")
        for lancamento in Lancamento.query.all():
            if (lancamento.tipo or "").strip().lower() in {"saída", "saida"}:
                total += Decimal(str(lancamento.valor or 0))
        return total.quantize(Decimal("0.01"))

    def _criar_entradas_base_admin(self, mes, ano, dizimos=0.0, ofertas=0.0, outras_ofertas=0.0, omn=0.0):
        entradas = []
        if dizimos:
            entradas.append(("DÍZIMO", dizimos, "Dízimos"))
        if ofertas:
            entradas.append(("OFERTA", ofertas, "Ofertas Alçadas"))
        if outras_ofertas:
            entradas.append(("OUTRAS OFERTAS", outras_ofertas, "Outras Ofertas"))
        if omn:
            entradas.append(("OFERTA OMN", omn, "Oferta Missionária"))

        for categoria, valor, descricao in entradas:
            db.session.add(
                Lancamento(
                    data=date(ano, mes, 5),
                    tipo="Entrada",
                    categoria=categoria,
                    descricao=descricao,
                    valor=float(valor),
                    conta="Banco",
                    origem="manual",
                )
            )
        db.session.commit()

    def test_caso_a_sem_pagamentos(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")
        obrigacao.atualizar_status()
        db.session.commit()

        self.assertEqual(obrigacao.valor_pago, Decimal("0.00"))
        self.assertEqual(obrigacao.valor_pendente, Decimal("1000.00"))
        self.assertEqual(obrigacao.status, "PENDENTE")

    def test_caso_b_pagamento_parcial(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")
        pagamento = self._novo_pagamento(valor="400.00")

        pagamento.adicionar_item(obrigacao, Decimal("400.00"))
        pagamento.validar_limite_alocacao()
        obrigacao.atualizar_status()
        db.session.commit()

        self.assertEqual(obrigacao.valor_pago, Decimal("400.00"))
        self.assertEqual(obrigacao.valor_pendente, Decimal("600.00"))
        self.assertEqual(obrigacao.status, "PARCIAL")

    def test_caso_c_quitacao_com_segundo_pagamento(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")

        pagamento1 = self._novo_pagamento(valor="400.00")
        pagamento1.adicionar_item(obrigacao, Decimal("400.00"))
        pagamento1.validar_limite_alocacao()

        pagamento2 = self._novo_pagamento(valor="600.00")
        pagamento2.adicionar_item(obrigacao, Decimal("600.00"))
        pagamento2.validar_limite_alocacao()

        obrigacao.atualizar_status()
        db.session.commit()

        self.assertEqual(obrigacao.valor_pago, Decimal("1000.00"))
        self.assertEqual(obrigacao.valor_pendente, Decimal("0.00"))
        self.assertEqual(obrigacao.status, "PAGO")
        self.assertIsNotNone(obrigacao.data_quitacao)

    def test_caso_d_bloqueia_pagamento_acima_do_saldo(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")

        pagamento1 = self._novo_pagamento(valor="400.00")
        pagamento1.adicionar_item(obrigacao, Decimal("400.00"))
        pagamento1.validar_limite_alocacao()
        obrigacao.atualizar_status()

        pagamento2 = self._novo_pagamento(valor="700.00")
        with self.assertRaises(ValueError):
            pagamento2.adicionar_item(obrigacao, Decimal("700.00"))

    def test_caso_e_rateio_um_pagamento_duas_obrigacoes(self):
        obrigacao_a = self._nova_obrigacao(valor="1000.00", descricao="Obrigação A")
        obrigacao_b = self._nova_obrigacao(valor="1000.00", descricao="Obrigação B")

        pagamento = self._novo_pagamento(valor="1000.00")
        pagamento.adicionar_item(obrigacao_a, Decimal("400.00"))
        pagamento.adicionar_item(obrigacao_b, Decimal("600.00"))
        pagamento.validar_limite_alocacao()

        obrigacao_a.atualizar_status()
        obrigacao_b.atualizar_status()
        db.session.commit()

        self.assertEqual(pagamento.valor_alocado_total, Decimal("1000.00"))
        self.assertEqual(obrigacao_a.valor_pago, Decimal("400.00"))
        self.assertEqual(obrigacao_b.valor_pago, Decimal("600.00"))
        self.assertEqual(obrigacao_a.status, "PARCIAL")
        self.assertEqual(obrigacao_b.status, "PARCIAL")

    def test_caso_f_historico_sem_movimentacao_sem_lancamento(self):
        self._nova_obrigacao(valor="1000.00")
        pagamento = self._novo_pagamento(valor="1000.00", tipo_pagamento="HISTORICO_SEM_MOVIMENTACAO", lancamento_id=None)
        db.session.commit()

        self.assertIsNone(pagamento.lancamento_financeiro_id)

    def test_caso_g_pagamento_bancario_com_lancamento(self):
        lancamento = Lancamento(
            data=date(2026, 7, 3),
            tipo="Saída",
            categoria="REPASSE À SEDE",
            descricao="Pagamento bancário de teste",
            valor=1000.0,
            conta="Banco",
            origem="manual",
        )
        db.session.add(lancamento)
        db.session.flush()

        pagamento = self._novo_pagamento(valor="1000.00", tipo_pagamento="PAGAMENTO_BANCARIO", lancamento_id=lancamento.id)
        db.session.commit()

        self.assertEqual(pagamento.lancamento_financeiro_id, lancamento.id)
        self.assertIsNotNone(pagamento.lancamento_financeiro)

    def test_caso_h_competencia_mes_invalida(self):
        with self.assertRaises(ValueError):
            self._nova_obrigacao(valor="1000.00", competencia_mes=13)

    def test_caso_i_valor_devido_invalido(self):
        with self.assertRaises(ValueError):
            self._nova_obrigacao(valor="0.00")

    def test_caso_j_bloqueia_duplicidade_automatica(self):
        self._nova_obrigacao(
            valor="1200.00",
            tipo_obrigacao="ADMIN_SEDE_30",
            origem_obrigacao="automatico",
            referencia_origem_tipo="FECHAMENTO_MENSAL",
            referencia_origem_id=1,
            competencia_mes=7,
            competencia_ano=2026,
            descricao="30% julho",
        )

        duplicada = ObrigacaoFinanceira(
            tipo_obrigacao="ADMIN_SEDE_30",
            origem_obrigacao="automatico",
            referencia_origem_tipo="FECHAMENTO_MENSAL",
            referencia_origem_id=1,
            categoria="CONTRIB. SEDE",
            descricao="30% julho duplicado",
            competencia_mes=7,
            competencia_ano=2026,
            valor_devido=Decimal("1200.00"),
            status="PENDENTE",
        )
        duplicada.validar()

        with self.assertRaises(ValueError):
            duplicada.validar_duplicidade_automatica(db.session)

    def test_caso_k_pago_para_parcial_mesma_sessao(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")

        pagamento_1 = self._novo_pagamento(valor="600.00")
        pagamento_1.adicionar_item(obrigacao, Decimal("600.00"))

        pagamento_2 = self._novo_pagamento(valor="400.00")
        item_2 = pagamento_2.adicionar_item(obrigacao, Decimal("400.00"))

        obrigacao.recalcular_em_sessao(flush=True)
        self.assertEqual(obrigacao.status, "PAGO")
        self.assertEqual(obrigacao.valor_pago, Decimal("1000.00"))

        pagamento_2.remover_item(item_2, flush=False)
        self.assertEqual(obrigacao.valor_pago, Decimal("600.00"))
        self.assertEqual(obrigacao.valor_pendente, Decimal("400.00"))
        self.assertEqual(obrigacao.status, "PARCIAL")

        db.session.flush()
        self.assertEqual(obrigacao.valor_pago, Decimal("600.00"))
        self.assertEqual(obrigacao.valor_pendente, Decimal("400.00"))
        self.assertEqual(obrigacao.status, "PARCIAL")

        db.session.commit()
        obrigacao_db = db.session.get(ObrigacaoFinanceira, obrigacao.id)
        obrigacao_db.recalcular_em_sessao(flush=False)
        self.assertEqual(obrigacao_db.valor_pago, Decimal("600.00"))
        self.assertEqual(obrigacao_db.valor_pendente, Decimal("400.00"))
        self.assertEqual(obrigacao_db.status, "PARCIAL")

    def test_caso_l_data_quitacao_limpa_ao_reverter_para_parcial(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")
        pagamento_1 = self._novo_pagamento(valor="600.00")
        pagamento_1.adicionar_item(obrigacao, Decimal("600.00"))

        pagamento_2 = self._novo_pagamento(valor="400.00")
        item_2 = pagamento_2.adicionar_item(obrigacao, Decimal("400.00"))

        obrigacao.recalcular_em_sessao(flush=True)
        self.assertEqual(obrigacao.status, "PAGO")
        self.assertIsNotNone(obrigacao.data_quitacao)

        pagamento_2.remover_item(item_2, flush=False)
        self.assertEqual(obrigacao.status, "PARCIAL")
        self.assertIsNone(obrigacao.data_quitacao)

    def test_caso_m_exclusao_obrigacao_com_itens_bloqueada(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")
        pagamento = self._novo_pagamento(valor="300.00")
        pagamento.adicionar_item(obrigacao, Decimal("300.00"))
        db.session.flush()

        db.session.delete(obrigacao)
        with self.assertRaises(IntegrityError):
            db.session.flush()
        db.session.rollback()

    def test_caso_n_exclusao_pagamento_com_itens_bloqueada(self):
        obrigacao = self._nova_obrigacao(valor="1000.00")
        pagamento = self._novo_pagamento(valor="300.00")
        pagamento.adicionar_item(obrigacao, Decimal("300.00"))
        db.session.flush()

        db.session.delete(pagamento)
        with self.assertRaises(IntegrityError):
            db.session.flush()
        db.session.rollback()

    def test_caso_o_admin_sede_duplicado_mesma_competencia_bloqueado(self):
        obrigacao_1 = ObrigacaoFinanceira(
            tipo_obrigacao="ADMIN_SEDE_30",
            origem_obrigacao="automatico",
            referencia_origem_tipo="FECHAMENTO_MENSAL",
            referencia_origem_id=202607,
            categoria="CONTRIB. SEDE",
            descricao="30% julho",
            competencia_mes=7,
            competencia_ano=2026,
            valor_devido=Decimal("1200.00"),
            status="PENDENTE",
        )
        obrigacao_1.validar()
        obrigacao_1.validar_duplicidade_automatica(db.session)
        db.session.add(obrigacao_1)
        db.session.flush()

        obrigacao_2 = ObrigacaoFinanceira(
            tipo_obrigacao="ADMIN_SEDE_30",
            origem_obrigacao="automatico",
            referencia_origem_tipo="FECHAMENTO_MENSAL",
            referencia_origem_id=202607,
            categoria="CONTRIB. SEDE",
            descricao="30% julho duplicado",
            competencia_mes=7,
            competencia_ano=2026,
            valor_devido=Decimal("1200.00"),
            status="PENDENTE",
        )
        obrigacao_2.validar()
        with self.assertRaises(ValueError):
            obrigacao_2.validar_duplicidade_automatica(db.session)

    def test_caso_p_despesa_fixa_duplicada_mesma_referencia_bloqueada(self):
        obrigacao_1 = ObrigacaoFinanceira(
            tipo_obrigacao="DESPESA_FIXA",
            origem_obrigacao="automatico",
            referencia_origem_tipo="DESPESA_FIXA_CONSELHO",
            referencia_origem_id=10,
            categoria="DESP. FIXAS",
            descricao="Despesa fixa 07/2026",
            competencia_mes=7,
            competencia_ano=2026,
            valor_devido=Decimal("150.00"),
            status="PENDENTE",
        )
        obrigacao_1.validar()
        obrigacao_1.validar_duplicidade_automatica(db.session)
        db.session.add(obrigacao_1)
        db.session.flush()

        obrigacao_2 = ObrigacaoFinanceira(
            tipo_obrigacao="DESPESA_FIXA",
            origem_obrigacao="automatico",
            referencia_origem_tipo="DESPESA_FIXA_CONSELHO",
            referencia_origem_id=10,
            categoria="DESP. FIXAS",
            descricao="Despesa fixa 07/2026 duplicada",
            competencia_mes=7,
            competencia_ano=2026,
            valor_devido=Decimal("150.00"),
            status="PENDENTE",
        )
        obrigacao_2.validar()
        with self.assertRaises(ValueError):
            obrigacao_2.validar_duplicidade_automatica(db.session)

    def test_caso_q_outra_duplicada_permitida(self):
        obrigacao_1 = self._nova_obrigacao(
            valor="100.00",
            tipo_obrigacao="OUTRA",
            origem_obrigacao="manual",
            referencia_origem_tipo="MANUAL",
            referencia_origem_id=77,
            competencia_mes=7,
            competencia_ano=2026,
            descricao="Outra 1",
        )

        obrigacao_2 = ObrigacaoFinanceira(
            tipo_obrigacao="OUTRA",
            origem_obrigacao="manual",
            referencia_origem_tipo="MANUAL",
            referencia_origem_id=77,
            categoria="TESTE",
            descricao="Outra 2",
            competencia_mes=7,
            competencia_ano=2026,
            valor_devido=Decimal("200.00"),
            status="PENDENTE",
        )
        obrigacao_2.validar()
        obrigacao_2.validar_duplicidade_automatica(db.session)
        db.session.add(obrigacao_2)
        db.session.flush()

        self.assertIsNotNone(obrigacao_1.id)
        self.assertIsNotNone(obrigacao_2.id)

    def test_caso_r_gera_obrigacao_sem_lancamento(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=100.0)

        resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(resultado["erros"], [])
        self.assertEqual(resultado["criadas"], ["Internet Sede"])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 1)
        self.assertEqual(Lancamento.query.count(), 0)

        obrigacao = ObrigacaoFinanceira.query.first()
        self.assertEqual(obrigacao.tipo_obrigacao, "DESPESA_FIXA")
        self.assertEqual(obrigacao.origem_obrigacao, "automatico")
        self.assertEqual(obrigacao.referencia_origem_tipo, "DESPESA_FIXA_CONSELHO")
        self.assertEqual(obrigacao.referencia_origem_id, despesa.id)
        self.assertEqual(obrigacao.categoria, "DESP. FIXAS")
        self.assertEqual(obrigacao.descricao, "Internet Sede - Despesa Fixa 07/2026")
        self.assertEqual(obrigacao.competencia_mes, 7)
        self.assertEqual(obrigacao.competencia_ano, 2026)
        self.assertEqual(obrigacao.valor_devido, Decimal("100.00"))
        self.assertEqual(obrigacao.status, "PENDENTE")
        self.assertFalse(obrigacao.historico_sem_movimentacao)
        self.assertIsNone(getattr(obrigacao, "conta", None))

    def test_caso_s_idempotencia_mesmo_mes(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0)

        primeiro = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)
        segundo = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(primeiro["criadas"], ["Internet Sede"])
        self.assertEqual(segundo["criadas"], [])
        self.assertEqual(segundo["ja_existentes"], ["Internet Sede"])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 1)

    def test_caso_t_duas_despesas_mesmo_mes(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0)
        self._nova_despesa_fixa("Contabilidade", valor=250.0)

        resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(sorted(resultado["criadas"]), ["Contabilidade", "Internet Sede"])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 2)

    def test_caso_u_mes_diferente_permite_nova(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0)

        gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)
        gerar_obrigacoes_despesas_fixas(mes=8, ano=2026)

        self.assertEqual(ObrigacaoFinanceira.query.count(), 2)

    def test_caso_v_despesa_inativa_nao_gera(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0, ativa=False)

        resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(resultado["criadas"], [])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 0)

    def test_caso_w_saldo_inalterado_sem_lancamento(self):
        self._nova_despesa_fixa("Internet Sede", valor=300.0)
        lancamento_entrada = Lancamento(
            data=date(2026, 7, 1),
            tipo="Entrada",
            categoria="TESTE",
            descricao="Saldo inicial",
            valor=1000.0,
            conta="Banco",
            origem="manual",
        )
        db.session.add(lancamento_entrada)
        db.session.commit()

        saldo_antes = self._saldo_lancamentos()
        resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)
        saldo_depois = self._saldo_lancamentos()

        self.assertEqual(resultado["criadas"], ["Internet Sede"])
        self.assertEqual(saldo_antes, Decimal("1000.00"))
        self.assertEqual(saldo_depois, Decimal("1000.00"))
        self.assertEqual(ObrigacaoFinanceira.query.first().status, "PENDENTE")

    def test_caso_x_evento_criacao_registrado(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0)

        resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(resultado["erros"], [])
        evento = ObrigacaoEvento.query.first()
        self.assertIsNotNone(evento)
        self.assertEqual(evento.evento_tipo, "CRIACAO")
        self.assertIn('"origem": "automatico"', evento.payload_json)
        self.assertIn('"referencia_origem_id":', evento.payload_json)
        self.assertIn('"competencia": "07/2026"', evento.payload_json)
        self.assertIn('"valor_devido": "100.00"', evento.payload_json)

    def test_caso_y_erro_reverte_transacao(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0)
        self._nova_despesa_fixa("Contabilidade", valor=250.0)

        original_add = db.session.add

        def _add_com_falha(objeto):
            if isinstance(objeto, ObrigacaoEvento):
                raise RuntimeError("falha forçada no evento")
            return original_add(objeto)

        with patch.object(db.session, "add", side_effect=_add_com_falha):
            resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertTrue(resultado["erros"])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 0)
        self.assertEqual(ObrigacaoEvento.query.count(), 0)

    def test_caso_z_legacy_nao_cria_saida_automatica(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0)

        resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(resultado["criadas"], ["Internet Sede"])
        lancamentos_automaticos = Lancamento.query.filter(
            Lancamento.origem.ilike("automatico"),
            Lancamento.tipo.ilike("saída"),
        ).count()
        self.assertEqual(lancamentos_automaticos, 0)

    def test_caso_aa_mes_sem_despesas_nao_gera(self):
        resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(resultado["criadas"], [])
        self.assertEqual(resultado["ja_existentes"], [])
        self.assertEqual(resultado["erros"], [])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 0)
        self.assertEqual(ObrigacaoEvento.query.count(), 0)

    def test_caso_ab_snapshot_historico_preservado(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=100.0, descricao="Internet mensal", categoria="DESP. FIXAS")

        gerar_obrigacoes_despesas_fixas(mes=1, ano=2026)

        obrigacao_janeiro = ObrigacaoFinanceira.query.filter_by(competencia_mes=1, competencia_ano=2026).first()
        self.assertIsNotNone(obrigacao_janeiro)
        self.assertEqual(obrigacao_janeiro.valor_devido, Decimal("100.00"))
        self.assertEqual(obrigacao_janeiro.categoria, "DESP. FIXAS")
        self.assertEqual(obrigacao_janeiro.descricao, "Internet Sede - Despesa Fixa 01/2026")
        self.assertEqual(obrigacao_janeiro.referencia_origem_id, despesa.id)

        despesa.valor_padrao = 150.0
        despesa.categoria = "OUTRA CATEGORIA"
        despesa.descricao = "Internet atualizada"
        db.session.commit()

        obrigacao_janeiro_db = db.session.get(ObrigacaoFinanceira, obrigacao_janeiro.id)
        self.assertEqual(obrigacao_janeiro_db.valor_devido, Decimal("100.00"))
        self.assertEqual(obrigacao_janeiro_db.categoria, "DESP. FIXAS")
        self.assertEqual(obrigacao_janeiro_db.descricao, "Internet Sede - Despesa Fixa 01/2026")

        gerar_obrigacoes_despesas_fixas(mes=2, ano=2026)
        obrigacao_fevereiro = ObrigacaoFinanceira.query.filter_by(competencia_mes=2, competencia_ano=2026).first()
        self.assertIsNotNone(obrigacao_fevereiro)
        self.assertEqual(obrigacao_fevereiro.valor_devido, Decimal("150.00"))
        self.assertEqual(obrigacao_fevereiro.categoria, "OUTRA CATEGORIA")
        self.assertEqual(obrigacao_fevereiro.descricao, "Internet Sede - Despesa Fixa 02/2026")

    def test_caso_ab1_helper_sem_commit_cria_obrigacao(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=100.0)

        retorno = _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=7, ano=2026)

        self.assertEqual(retorno["status"], "criada")
        self.assertIsNotNone(retorno["obrigacao"])
        self.assertIsNotNone(retorno["obrigacao"].id)
        self.assertEqual(ObrigacaoFinanceira.query.count(), 1)

        db.session.rollback()
        self.assertEqual(ObrigacaoFinanceira.query.count(), 0)

    def test_caso_ab2_helper_sem_commit_cria_evento(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=100.0)

        retorno = _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=7, ano=2026)

        self.assertEqual(retorno["status"], "criada")
        self.assertEqual(ObrigacaoEvento.query.count(), 1)
        evento = ObrigacaoEvento.query.first()
        self.assertEqual(evento.evento_tipo, "CRIACAO")
        self.assertIn('"competencia": "07/2026"', evento.payload_json)

    def test_caso_ab3_helper_idempotente_mesma_competencia(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=100.0)

        primeiro = _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=7, ano=2026)
        segundo = _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=7, ano=2026)

        self.assertEqual(primeiro["status"], "criada")
        self.assertEqual(segundo["status"], "ja_existente")
        self.assertEqual(ObrigacaoFinanceira.query.count(), 1)
        self.assertEqual(ObrigacaoEvento.query.count(), 1)

    def test_caso_ab4_orquestrador_commit_unico_ao_final(self):
        self._nova_despesa_fixa("Internet Sede", valor=100.0)
        self._nova_despesa_fixa("Contabilidade", valor=250.0)

        original_commit = db.session.commit
        with patch.object(db.session, "commit", wraps=original_commit) as commit_spy:
            resultado = gerar_obrigacoes_despesas_fixas(mes=7, ano=2026)

        self.assertEqual(resultado["erros"], [])
        self.assertEqual(len(resultado["criadas"]), 2)
        self.assertEqual(commit_spy.call_count, 1)
        self.assertEqual(ObrigacaoFinanceira.query.count(), 2)

    def test_caso_ab5_helper_nunca_cria_lancamento(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=100.0)

        _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=7, ano=2026)

        self.assertEqual(Lancamento.query.count(), 0)

    def test_caso_ab6_smoke_transacional_local_sem_commit(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=300.0)
        lancamento_entrada = Lancamento(
            data=date(2026, 7, 1),
            tipo="Entrada",
            categoria="TESTE",
            descricao="Saldo inicial",
            valor=1000.0,
            conta="Banco",
            origem="manual",
        )
        db.session.add(lancamento_entrada)
        db.session.commit()

        counts_antes = {
            "obrigacoes": ObrigacaoFinanceira.query.count(),
            "eventos": ObrigacaoEvento.query.count(),
            "lancamentos": Lancamento.query.count(),
            "pagamentos": PagamentoObrigacao.query.count(),
            "itens": PagamentoObrigacaoItem.query.count(),
        }
        saldo_antes = self._saldo_lancamentos()

        primeiro = _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=12, ano=2099)
        segundo = _criar_obrigacao_despesa_fixa_sem_commit(despesa=despesa, mes=12, ano=2099)

        self.assertEqual(primeiro["status"], "criada")
        self.assertEqual(segundo["status"], "ja_existente")
        self.assertEqual(self._saldo_lancamentos(), saldo_antes)

        db.session.rollback()

        counts_depois = {
            "obrigacoes": ObrigacaoFinanceira.query.count(),
            "eventos": ObrigacaoEvento.query.count(),
            "lancamentos": Lancamento.query.count(),
            "pagamentos": PagamentoObrigacao.query.count(),
            "itens": PagamentoObrigacaoItem.query.count(),
        }
        saldo_depois = self._saldo_lancamentos()

        self.assertEqual(counts_antes, counts_depois)
        self.assertEqual(saldo_antes, saldo_depois)

    def test_caso_ac_inativa_reativada_sem_afetar_histórico(self):
        despesa = self._nova_despesa_fixa("Internet Sede", valor=100.0, ativa=False)

        resultado_inativa = gerar_obrigacoes_despesas_fixas(mes=3, ano=2026)
        self.assertEqual(resultado_inativa["criadas"], [])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 0)

        despesa.ativo = True
        db.session.commit()

        resultado_reativada = gerar_obrigacoes_despesas_fixas(mes=4, ano=2026)
        self.assertEqual(resultado_reativada["criadas"], ["Internet Sede"])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 1)

        despesa.ativo = False
        db.session.commit()

        obrigacao_apurada = ObrigacaoFinanceira.query.first()
        self.assertIsNotNone(obrigacao_apurada)
        self.assertEqual(obrigacao_apurada.valor_devido, Decimal("100.00"))
        self.assertEqual(obrigacao_apurada.status, "PENDENTE")

    def test_caso_ad_geracao_atomica_rollback_total(self):
        self._nova_despesa_fixa("Despesa A", valor=100.0)
        self._nova_despesa_fixa("Despesa B", valor=80.0)
        self._nova_despesa_fixa("Despesa C", valor=60.0)

        original_add = db.session.add
        contador_obrigacoes = {"total": 0}

        def _add_com_falha_na_terceira_obrigacao(objeto):
            if isinstance(objeto, ObrigacaoFinanceira):
                contador_obrigacoes["total"] += 1
                if contador_obrigacoes["total"] == 3:
                    raise RuntimeError("falha controlada na terceira obrigacao")
            return original_add(objeto)

        with patch.object(db.session, "add", side_effect=_add_com_falha_na_terceira_obrigacao):
            resultado = gerar_obrigacoes_despesas_fixas(mes=5, ano=2026)

        self.assertTrue(resultado["erros"])
        self.assertEqual(ObrigacaoFinanceira.query.count(), 0)
        self.assertEqual(ObrigacaoEvento.query.count(), 0)

    def test_caso_ae_admin_a_cria_obrigacao_sem_lancamento(self):
        config = Configuracao.obter_configuracao()
        config.percentual_conselho = 25.0
        db.session.commit()

        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=2500.0, ofertas=1500.0)
        saldo_antes = self._saldo_lancamentos()
        lancamentos_antes = Lancamento.query.count()

        resultado = gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        self.assertEqual(resultado["status"], "criada")
        self.assertEqual(ObrigacaoFinanceira.query.count(), 1)
        self.assertEqual(ObrigacaoEvento.query.count(), 1)
        obrigacao = ObrigacaoFinanceira.query.first()
        self.assertEqual(obrigacao.tipo_obrigacao, "ADMIN_SEDE_30")
        self.assertEqual(obrigacao.status, "PENDENTE")
        self.assertEqual(obrigacao.valor_devido, Decimal("1000.00"))
        self.assertEqual(obrigacao.categoria, "CONTRIB. SEDE")
        self.assertEqual(Lancamento.query.count(), lancamentos_antes)
        self.assertEqual(self._saldo_lancamentos(), saldo_antes)

    def test_caso_af_admin_b_reexecucao_mesma_competencia_idempotente(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)

        primeiro = gerar_obrigacao_admin_sede_30(mes=7, ano=2026)
        segundo = gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        self.assertEqual(primeiro["status"], "criada")
        self.assertEqual(segundo["status"], "ja_existente")
        self.assertEqual(ObrigacaoFinanceira.query.count(), 1)

    def test_caso_ag_admin_c_mes_diferente_permite_nova(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)
        self._criar_entradas_base_admin(mes=8, ano=2026, dizimos=1200.0, ofertas=1800.0)

        r1 = gerar_obrigacao_admin_sede_30(mes=7, ano=2026)
        r2 = gerar_obrigacao_admin_sede_30(mes=8, ano=2026)

        self.assertEqual(r1["status"], "criada")
        self.assertEqual(r2["status"], "criada")
        self.assertEqual(ObrigacaoFinanceira.query.count(), 2)

    def test_caso_ah_admin_d_evento_criacao_um(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)

        gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        eventos = ObrigacaoEvento.query.all()
        self.assertEqual(len(eventos), 1)
        self.assertEqual(eventos[0].evento_tipo, "CRIACAO")
        self.assertIn('"tipo_obrigacao": "ADMIN_SEDE_30"', eventos[0].payload_json)
        self.assertIn('"competencia": "07/2026"', eventos[0].payload_json)

    def test_caso_ai_admin_e_sem_evento_duplicado(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)

        gerar_obrigacao_admin_sede_30(mes=7, ano=2026)
        gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        self.assertEqual(ObrigacaoEvento.query.count(), 1)

    def test_caso_aj_admin_f_g_sem_pagamentos_ou_itens(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)

        gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        self.assertEqual(PagamentoObrigacao.query.count(), 0)
        self.assertEqual(PagamentoObrigacaoItem.query.count(), 0)

    def test_caso_ak_admin_h_sem_alterar_envio_sede(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)
        envios_antes = EnvioSede.query.count()

        gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        self.assertEqual(EnvioSede.query.count(), envios_antes)

    def test_caso_al_admin_i_j_saldo_e_saidas_inalterados(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1200.0, ofertas=1800.0)
        db.session.add(
            Lancamento(
                data=date(2026, 7, 7),
                tipo="Saída",
                categoria="DESP. VARIAVEIS",
                descricao="Saída manual",
                valor=500.0,
                conta="Banco",
                origem="manual",
            )
        )
        db.session.commit()

        saldo_antes = self._saldo_lancamentos()
        saidas_antes = self._total_saidas_lancamentos()

        gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        self.assertEqual(self._saldo_lancamentos(), saldo_antes)
        self.assertEqual(self._total_saidas_lancamentos(), saidas_antes)

    def test_caso_am_admin_k_equivalencia_formula_legado(self):
        config = Configuracao.obter_configuracao()
        config.percentual_conselho = 30.0
        db.session.commit()

        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0, outras_ofertas=400.0, omn=500.0)

        calculo_legado = _calcular_admin_sede_30_legado(7, 2026, 30.0)
        resultado = gerar_obrigacao_admin_sede_30(mes=7, ano=2026)
        obrigacao = ObrigacaoFinanceira.query.first()

        valor_30_legado = Decimal(str(calculo_legado["valor_conselho"])).quantize(Decimal("0.01"))
        valor_obrigacao_nova = obrigacao.valor_devido
        diferenca = abs(valor_30_legado - valor_obrigacao_nova)

        self.assertEqual(resultado["status"], "criada")
        self.assertEqual(diferenca, Decimal("0.00"))

    def test_caso_an_admin_l_falha_controlada_rollback_total(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)

        original_add = db.session.add

        def _add_com_falha_evento(objeto):
            if isinstance(objeto, ObrigacaoEvento):
                raise RuntimeError("falha controlada no evento admin")
            return original_add(objeto)

        with patch.object(db.session, "add", side_effect=_add_com_falha_evento):
            resultado = gerar_obrigacao_admin_sede_30(mes=7, ano=2026)

        self.assertEqual(resultado["status"], "erro")
        self.assertEqual(ObrigacaoFinanceira.query.count(), 0)
        self.assertEqual(ObrigacaoEvento.query.count(), 0)

    def test_caso_ao_admin_m_helper_transacao_externa_persistencia_zero(self):
        self._criar_entradas_base_admin(mes=7, ano=2026, dizimos=1000.0, ofertas=2000.0)
        calculo = _calcular_admin_sede_30_legado(7, 2026, 30.0)

        counts_antes = {
            "obrigacoes": ObrigacaoFinanceira.query.count(),
            "eventos": ObrigacaoEvento.query.count(),
            "lancamentos": Lancamento.query.count(),
            "pagamentos": PagamentoObrigacao.query.count(),
            "itens": PagamentoObrigacaoItem.query.count(),
            "envios": EnvioSede.query.count(),
        }

        primeiro = _criar_obrigacao_admin_sede_sem_commit(7, 2026, 30.0, calculo)
        segundo = _criar_obrigacao_admin_sede_sem_commit(7, 2026, 30.0, calculo)

        self.assertEqual(primeiro["status"], "criada")
        self.assertEqual(segundo["status"], "ja_existente")

        db.session.flush()
        db.session.rollback()

        counts_depois = {
            "obrigacoes": ObrigacaoFinanceira.query.count(),
            "eventos": ObrigacaoEvento.query.count(),
            "lancamentos": Lancamento.query.count(),
            "pagamentos": PagamentoObrigacao.query.count(),
            "itens": PagamentoObrigacaoItem.query.count(),
            "envios": EnvioSede.query.count(),
        }

        self.assertEqual(counts_antes, counts_depois)

    def test_caso_r_startup_nao_cria_tabelas_novas(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        database_url = f"sqlite:///{db_path.replace('\\', '/')}"

        try:
            env = os.environ.copy()
            env["DATABASE_URL"] = database_url
            env["PYTHONPATH"] = "."

            probe_script = """
from app import create_app
from app.extensoes import db
from sqlalchemy import inspect
app = create_app()
with app.app_context():
    insp = inspect(db.engine)
    alvo = {'obrigacoes_financeiras','pagamentos_obrigacao','pagamentos_obrigacao_itens','obrigacao_eventos'}
    existentes = set(insp.get_table_names())
    inter = sorted(alvo.intersection(existentes))
    print(','.join(inter))
"""

            proc = subprocess.run(
                [sys.executable, "-c", probe_script],
                cwd=str(self._project_root()),
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
            saida = (proc.stdout or "").strip()
            self.assertEqual(saida, "", msg=f"tabelas novas criadas no startup: {saida}")
        finally:
            try:
                os.remove(db_path)
            except OSError:
                pass

    def test_caso_s_script_schema_cria_tabelas(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        database_url = f"sqlite:///{db_path.replace('\\', '/')}"
        try:
            run_result = self._run_schema_script(database_url)
            self.assertEqual(run_result.returncode, 0, msg=run_result.stdout + "\n" + run_result.stderr)

            check_app = Flask(__name__)
            check_app.config["SQLALCHEMY_DATABASE_URI"] = database_url
            check_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
            db.init_app(check_app)
            with check_app.app_context():
                insp = inspect(db.engine)
                tabelas = set(insp.get_table_names())
                self.assertTrue(self.NOVAS_TABELAS.issubset(tabelas))
        finally:
            try:
                os.remove(db_path)
            except OSError:
                pass

    def test_caso_t_script_schema_idempotente(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        database_url = f"sqlite:///{db_path.replace('\\', '/')}"
        try:
            first_run = self._run_schema_script(database_url)
            self.assertEqual(first_run.returncode, 0, msg=first_run.stdout + "\n" + first_run.stderr)

            second_run = self._run_schema_script(database_url)
            self.assertEqual(second_run.returncode, 0, msg=second_run.stdout + "\n" + second_run.stderr)

            check_app = Flask(__name__)
            check_app.config["SQLALCHEMY_DATABASE_URI"] = database_url
            check_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
            db.init_app(check_app)
            with check_app.app_context():
                insp = inspect(db.engine)
                tabelas = set(insp.get_table_names())
                self.assertTrue(self.NOVAS_TABELAS.issubset(tabelas))
        finally:
            try:
                os.remove(db_path)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
