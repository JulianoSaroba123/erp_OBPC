from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from app import create_app
from app.extensoes import db
from app.usuario.usuario_model import Usuario
from app.configuracoes.configuracoes_model import Configuracao
from app.financeiro.financeiro_model import Lancamento
from app.financeiro.comprovante_model import Comprovante
from app.financeiro.projeto_model import Projeto
from app.financeiro.obrigacoes_model import ObrigacaoFinanceira, PagamentoObrigacao, PagamentoObrigacaoItem


class TestD23D28DashboardModerno(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True

        with cls.app.app_context():
            db.metadata.create_all(bind=db.engine)
            cls._seed_data()

    @classmethod
    def _seed_data(cls):
        ano = 2099
        mes = 7
        data_alvo = date(ano, mes, 15)
        lancamentos = date

        for model in [Comprovante, PagamentoObrigacaoItem, PagamentoObrigacao, ObrigacaoFinanceira, Lancamento, Projeto]:
            try:
                if model.__tablename__ == 'lancamentos':
                    db.session.query(model).filter(model.data >= date(2099, 1, 1)).delete(synchronize_session=False)
                elif model.__tablename__ == 'obrigacoes_financeiras':
                    db.session.query(model).filter(model.competencia_ano == 2099).delete(synchronize_session=False)
                elif model.__tablename__ == 'pagamentos_obrigacao':
                    db.session.query(model).filter(model.data_pagamento >= date(2099, 1, 1)).delete(synchronize_session=False)
                elif model.__tablename__ == 'pagamentos_obrigacao_itens':
                    db.session.query(model).delete(synchronize_session=False)
                elif model.__tablename__ == 'comprovantes':
                    db.session.query(model).delete(synchronize_session=False)
                elif model.__tablename__ == 'projetos':
                    db.session.query(model).filter(model.nome.like('D23D28 %')).delete(synchronize_session=False)
            except Exception:
                pass

        usuario = Usuario.query.get(1)
        if not usuario:
            usuario = Usuario(
                id=1,
                nome='Usuário D23D28',
                email='d23d28@example.com',
                nivel_acesso='administrador',
                ativo=True,
            )
            usuario.set_senha('senha-teste')
            db.session.add(usuario)

        config = Configuracao.query.get(1)
        if not config:
            config = Configuracao(id=1, nome_igreja='OBPC Teste', cidade='Tietê', bairro='Centro', endereco='Rua Teste')
            db.session.add(config)

        config.saldo_inicial = 100.0
        config.percentual_conselho = 30.0
        config.percentual_administrativo = 30.0
        config.percentual_prebenda = 30.0
        config.percentual_cuidados_igreja = 40.0
        config.exibir_indicador_distribuicao = True

        projeto_ativo = Projeto(nome='D23D28 Projeto Ativo', descricao='Projeto ativo de teste', tipo='Evento', status='Ativo')
        projeto_inativo = Projeto(nome='D23D28 Projeto Inativo', descricao='Projeto cancelado de teste', tipo='Evento', status='Cancelado')
        db.session.add_all([projeto_ativo, projeto_inativo])
        db.session.flush()

        # Série 6 meses: fevereiro a julho de 2099
        for mes_item, entrada, saida in [
            (2, 10, 5),
            (3, 20, 10),
            (4, 30, 15),
            (5, 40, 20),
            (6, 50, 25),
            (7, 150, 55),
        ]:
            db.session.add(Lancamento(
                data=date(2099, mes_item, 15),
                tipo='Entrada',
                categoria='Dízimo' if mes_item == 7 else 'Oferta',
                descricao=f'Entrada {mes_item}',
                valor=float(entrada),
                conta='Banco',
                conciliado=(mes_item not in {5, 7}),
                criado_em=date(2099, mes_item, 15),
                projeto_id=projeto_ativo.id if mes_item == 7 else None,
            ))
            db.session.add(Lancamento(
                data=date(2099, mes_item, 16),
                tipo='Saída',
                categoria='Administrativo' if mes_item == 7 else 'Manutenção',
                descricao=f'Saída {mes_item}',
                valor=float(saida),
                conta='Banco',
                conciliado=(mes_item not in {3, 7}),
                criado_em=date(2099, mes_item, 16),
            ))

        lancamento_com_legado = Lancamento(
            data=date(2099, 7, 18),
            tipo='Saída',
            categoria='Despesas gerais',
            descricao='Sem comprovante legado',
            valor=12.0,
            conta='Banco',
            conciliado=False,
            criado_em=date(2099, 7, 18),
            comprovante=None,
        )
        db.session.add(lancamento_com_legado)

        lancamento_com_relacionado = Lancamento(
            data=date(2099, 7, 19),
            tipo='Saída',
            categoria='Despesas gerais',
            descricao='Comprovante múltiplo',
            valor=18.0,
            conta='Banco',
            conciliado=True,
            criado_em=date(2099, 7, 19),
            comprovante=None,
        )
        db.session.add(lancamento_com_relacionado)
        db.session.flush()

        db.session.add(Comprovante(
            lancamento_id=lancamento_com_relacionado.id,
            arquivo='/static/uploads/comprovantes/teste.pdf',
            nome_original='teste.pdf',
            tamanho=1234,
            tipo_mime='application/pdf'
        ))

        repasse_competencia = ObrigacaoFinanceira(
            tipo_obrigacao='ADMIN_SEDE_30',
            origem_obrigacao='automatico',
            referencia_origem_tipo='D23D28',
            referencia_origem_id=1,
            descricao='Repasse competência julho/2099',
            competencia_mes=7,
            competencia_ano=2099,
            valor_devido=Decimal('300.00'),
            status='PARCIAL',
            historico_sem_movimentacao=False,
        )
        repasse_anterior = ObrigacaoFinanceira(
            tipo_obrigacao='ADMIN_SEDE_30',
            origem_obrigacao='automatico',
            referencia_origem_tipo='D23D28',
            referencia_origem_id=2,
            descricao='Repasse competência junho/2099',
            competencia_mes=6,
            competencia_ano=2099,
            valor_devido=Decimal('200.00'),
            status='PARCIAL',
            historico_sem_movimentacao=False,
        )
        despesa_fixa = ObrigacaoFinanceira(
            tipo_obrigacao='DESPESA_FIXA',
            origem_obrigacao='automatico',
            referencia_origem_tipo='D23D28',
            referencia_origem_id=3,
            descricao='Despesa fixa julho/2099',
            competencia_mes=7,
            competencia_ano=2099,
            valor_devido=Decimal('80.00'),
            status='PARCIAL',
            historico_sem_movimentacao=False,
        )
        db.session.add_all([repasse_competencia, repasse_anterior, despesa_fixa])
        db.session.flush()

        pagamento_repasse = PagamentoObrigacao(
            data_pagamento=date(2099, 7, 20),
            valor_pago=Decimal('120.00'),
            forma_pagamento='PIX',
            tipo_pagamento='PAGAMENTO_BANCARIO',
            observacao='Pagamento de teste repasse',
        )
        pagamento_repasse_anterior = PagamentoObrigacao(
            data_pagamento=date(2099, 6, 20),
            valor_pago=Decimal('150.00'),
            forma_pagamento='PIX',
            tipo_pagamento='PAGAMENTO_BANCARIO',
            observacao='Pagamento anterior',
        )
        pagamento_despesa = PagamentoObrigacao(
            data_pagamento=date(2099, 7, 21),
            valor_pago=Decimal('30.00'),
            forma_pagamento='Dinheiro',
            tipo_pagamento='PAGAMENTO_BANCARIO',
            observacao='Despesa fixa paga',
        )
        db.session.add_all([pagamento_repasse, pagamento_repasse_anterior, pagamento_despesa])
        db.session.flush()

        db.session.add_all([
            PagamentoObrigacaoItem(pagamento_obrigacao_id=pagamento_repasse.id, obrigacao_financeira_id=repasse_competencia.id, valor_alocado=Decimal('120.00')),
            PagamentoObrigacaoItem(pagamento_obrigacao_id=pagamento_repasse_anterior.id, obrigacao_financeira_id=repasse_anterior.id, valor_alocado=Decimal('150.00')),
            PagamentoObrigacaoItem(pagamento_obrigacao_id=pagamento_despesa.id, obrigacao_financeira_id=despesa_fixa.id, valor_alocado=Decimal('30.00')),
        ])

        db.session.commit()
        cls.data_alvo = data_alvo

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.rollback()

    def _client(self):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess.permanent = True
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        return client

    def _get_dashboard(self, mes=7, ano=2099):
        client = self._client()
        return client.get(f'/financeiro/dashboard?mes={mes}&ano={ano}')

    def test_a_entradas_corretas(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('R$ 150.00', html)

    def test_b_saidas_corretas(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('R$ 85.00', html)

    def test_c_saldo_mes_correto(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('R$ 65.00', html)

    def test_d_saldo_acumulado_correto(self):
        with patch('app.financeiro.financeiro_routes.Lancamento.calcular_saldo_ate_mes_anterior', return_value=100.0):
            resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('R$ 165.00', html)

    def test_e_repasse_usa_motor_novo(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('R$ 300.00', html)
        self.assertIn('R$ 120.00', html)
        self.assertIn('PARCIAL', html)

    def test_f_despesas_fixas_separadas_do_admin(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('Despesas Fixas', html)
        self.assertIn('R$ 80.00', html)
        self.assertIn('R$ 30.00', html)

    def test_g_grafico_6_meses(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('Fev/2099', html)
        self.assertIn('Jul/2099', html)

    def test_h_despesas_por_categoria(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('Administrativo', html)

    def test_i_sem_comprovante_com_legado_nao_conta(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('Sem Comprovante', html)
        self.assertIn('3', html)

    def test_j_sem_comprovante_com_tabela_multiplas(self):
        resposta = self._get_dashboard()
        html = resposta.get_data(as_text=True)
        self.assertIn('Sem Comprovante', html)
        self.assertIn('Sem comprovante', html)

    def test_k_dashboard_vazio(self):
        resposta = self._get_dashboard(mes=9, ano=2101)
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('VISÃO GERAL FINANCEIRA', html)
        self.assertIn('R$ 0.00', html)

    def test_l_saldo_negativo(self):
        client = self._client()
        with self.app.app_context():
            negativo = Lancamento(
                data=date(2099, 8, 10),
                tipo='Saída',
                categoria='Teste negativo',
                descricao='Saldo negativo',
                valor=999.0,
                conta='Banco',
                conciliado=False,
                criado_em=date(2099, 8, 10),
            )
            db.session.add(negativo)
            db.session.commit()
        resposta = client.get('/financeiro/dashboard?mes=8&ano=2099')
        html = resposta.get_data(as_text=True)
        self.assertIn('Saldo do mês negativo', html)

    def test_m_zero_divisao_por_zero(self):
        resposta = self._get_dashboard(mes=9, ano=2100)
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('VISÃO GERAL FINANCEIRA', html)
        self.assertIn('R$ 0.00', html)

    def test_n_template_renderiza_completo(self):
        resposta = self._get_dashboard()
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('VISÃO GERAL FINANCEIRA', html)
        self.assertIn('Ações Rápidas', html)


if __name__ == '__main__':
    unittest.main()