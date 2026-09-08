from datetime import date
import unittest

from flask import Flask

from app.extensoes import db
from app.financeiro.financeiro_model import (
    Lancamento,
    ConciliacaoHistorico,
    ConciliacaoPar,
)
from app.financeiro.projeto_model import Projeto
from app.financeiro.comprovante_model import Comprovante
from app.financeiro.utils.conciliacao_avancada import ConciliadorAvancado


class TestD23D48ConciliacaoRepasse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

        db.session.query(ConciliacaoPar).delete()
        db.session.query(ConciliacaoHistorico).delete()
        db.session.query(Comprovante).delete()
        db.session.query(Lancamento).delete()
        db.session.query(Projeto).delete()
        db.session.commit()

    def tearDown(self):
        db.session.rollback()
        db.session.remove()
        self.ctx.pop()

    def _manual_repasse(self, valor, descricao='Pagamento composto de 5 obrigação(ões)'):
        lancamento = Lancamento(
            data=date(2026, 8, 28),
            tipo='Saída',
            categoria='CONTRIB. SEDE',
            descricao=descricao,
            valor=valor,
            conta='Pix',
            origem='manual',
            conciliado=False,
        )
        db.session.add(lancamento)
        db.session.flush()
        return lancamento

    def _importado(self, valor, descricao):
        lancamento = Lancamento(
            data=date(2026, 8, 28),
            tipo='Saída',
            categoria='Importação',
            descricao=descricao,
            valor=valor,
            conta='Extrato',
            origem='importado',
            conciliado=False,
            banco_origem='pagbank',
        )
        db.session.add(lancamento)
        db.session.flush()
        return lancamento

    def test_repasse_1302_56_concilia_cinco_linhas_sem_duplicar_saida(self):
        manual = self._manual_repasse(1302.56)
        importados = [
            self._importado(1122.56, 'PIX 30% ADMINISTRATIVO'),
            self._importado(100.00, 'PIX CONTADOR'),
            self._importado(50.00, 'PIX FORCA PARA VIVER'),
            self._importado(10.00, 'PIX PROJETO FILIPE'),
            self._importado(20.00, 'PIX SITE'),
        ]
        db.session.commit()

        # Antes da conciliação há dois registros econômicos do mesmo fato.
        self.assertAlmostEqual(Lancamento.calcular_totais()['saidas'], 2605.12, places=2)

        resultado = ConciliadorAvancado().conciliar_automatico('teste-d23d48')
        self.assertNotIn('erro', resultado)
        self.assertEqual(resultado['grupos_compostos'], 1)
        self.assertEqual(resultado['conciliados'], 5)

        db.session.expire_all()
        manual_db = Lancamento.query.get(manual.id)
        importados_db = [Lancamento.query.get(item.id) for item in importados]

        self.assertTrue(manual_db.conciliado)
        self.assertTrue(all(item.conciliado for item in importados_db))
        self.assertTrue(all(item.tipo == 'Evidência' for item in importados_db))
        self.assertTrue(all(item.tipo_bancario == 'Saída' for item in importados_db))
        self.assertTrue(all(item.impacta_financeiro is False for item in importados_db))

        # Os valores bancários continuam intactos para auditoria.
        self.assertEqual(
            [round(item.valor, 2) for item in importados_db],
            [1122.56, 100.00, 50.00, 10.00, 20.00],
        )

        # Economicamente, somente o lançamento interno de R$ 1.302,56 permanece como saída.
        self.assertAlmostEqual(Lancamento.calcular_totais()['saidas'], 1302.56, places=2)
        saidas_economicas = Lancamento.query.filter(Lancamento.tipo == 'Saída').all()
        self.assertEqual([item.id for item in saidas_economicas], [manual.id])

        pares = ConciliacaoPar.query.filter_by(
            lancamento_manual_id=manual.id,
            ativo=True,
        ).all()
        self.assertEqual(len(pares), 5)
        self.assertEqual(
            {par.lancamento_importado_id for par in pares},
            {item.id for item in importados},
        )
        self.assertTrue(all(par.regra_aplicada == 'composto_n_1_soma_exata' for par in pares))

    def test_importado_nao_conciliado_continua_impactando_financeiro(self):
        manual = self._manual_repasse(1302.56)
        for valor, descricao in [
            (1122.56, 'ADMIN'),
            (100.00, 'CONTADOR'),
            (50.00, 'FORCA'),
            (10.00, 'FILIPE'),
            (20.00, 'SITE'),
        ]:
            self._importado(valor, descricao)
        avulso = self._importado(75.00, 'COMPRA AVULSA SEM LANCAMENTO INTERNO')
        db.session.commit()

        resultado = ConciliadorAvancado().conciliar_automatico('teste-d23d48')
        self.assertEqual(resultado['grupos_compostos'], 1)

        db.session.expire_all()
        avulso_db = Lancamento.query.get(avulso.id)
        self.assertFalse(avulso_db.conciliado)
        self.assertEqual(avulso_db.tipo, 'Saída')
        self.assertTrue(avulso_db.impacta_financeiro)
        self.assertAlmostEqual(Lancamento.calcular_totais()['saidas'], 1377.56, places=2)

    def test_combinacao_ambigua_nao_e_conciliada_automaticamente(self):
        manual = self._manual_repasse(100.00)
        importados = [
            self._importado(60.00, 'ALFA'),
            self._importado(40.00, 'BETA'),
            self._importado(70.00, 'GAMA'),
            self._importado(30.00, 'DELTA'),
        ]
        db.session.commit()

        resultado = ConciliadorAvancado().conciliar_automatico('teste-d23d48')

        self.assertNotIn('erro', resultado)
        self.assertEqual(resultado['grupos_compostos'], 0)
        self.assertEqual(resultado['conciliados'], 0)
        self.assertTrue(any('mais de uma combinação' in item for item in resultado['log']))

        db.session.expire_all()
        self.assertFalse(Lancamento.query.get(manual.id).conciliado)
        self.assertTrue(all(not Lancamento.query.get(item.id).conciliado for item in importados))

    def test_desfazer_um_par_de_grupo_n_1_preserva_demais_vinculos(self):
        manual = self._manual_repasse(1302.56)
        importados = [
            self._importado(1122.56, 'ADMIN'),
            self._importado(100.00, 'CONTADOR'),
            self._importado(50.00, 'FORCA'),
            self._importado(10.00, 'FILIPE'),
            self._importado(20.00, 'SITE'),
        ]
        db.session.commit()

        ConciliadorAvancado().conciliar_automatico('teste-d23d48')
        pares = ConciliacaoPar.query.filter_by(
            lancamento_manual_id=manual.id,
            ativo=True,
        ).order_by(ConciliacaoPar.id.asc()).all()
        self.assertEqual(len(pares), 5)

        primeiro = pares[0]
        valor_primeiro_importado = primeiro.lancamento_importado.valor
        primeiro.desfazer()
        db.session.expire_all()

        # O manual continua conciliado enquanto ainda houver outros quatro pares ativos.
        self.assertTrue(Lancamento.query.get(manual.id).conciliado)
        importado_desfeito = Lancamento.query.get(primeiro.lancamento_importado_id)
        self.assertFalse(importado_desfeito.conciliado)
        self.assertEqual(importado_desfeito.tipo, 'Saída')
        self.assertAlmostEqual(
            Lancamento.calcular_totais()['saidas'],
            1302.56 + valor_primeiro_importado,
            places=2,
        )

        # Ao desfazer os demais vínculos, o manual volta a pendente apenas no último par.
        for par in ConciliacaoPar.query.filter_by(
            lancamento_manual_id=manual.id,
            ativo=True,
        ).all():
            par.desfazer()

        db.session.expire_all()
        self.assertFalse(Lancamento.query.get(manual.id).conciliado)
        self.assertTrue(all(not Lancamento.query.get(item.id).conciliado for item in importados))
        self.assertAlmostEqual(Lancamento.calcular_totais()['saidas'], 2605.12, places=2)

    def test_conciliacao_1_para_1_continua_funcionando(self):
        manual = self._manual_repasse(500.00, descricao='Repasse à Sede')
        importado = self._importado(500.00, 'PIX REPASSE SEDE')
        db.session.commit()

        resultado = ConciliadorAvancado().conciliar_automatico('teste-d23d48')
        self.assertNotIn('erro', resultado)
        self.assertEqual(resultado['grupos_compostos'], 0)
        self.assertEqual(resultado['conciliados'], 1)

        db.session.expire_all()
        self.assertTrue(Lancamento.query.get(manual.id).conciliado)
        importado_db = Lancamento.query.get(importado.id)
        self.assertTrue(importado_db.conciliado)
        self.assertEqual(importado_db.tipo, 'Evidência')
        self.assertEqual(importado_db.tipo_bancario, 'Saída')
        self.assertAlmostEqual(Lancamento.calcular_totais()['saidas'], 500.00, places=2)


if __name__ == '__main__':
    unittest.main()
