from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import normalizar_nomes_pdfs as normalizer


class NormalizacaoNomesPdfsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "PDF_AULAS"
        self.lesson_dir = (
            self.root / "BIOLOGIA" / "EM" / "3_BIMESTRE" / "2_ANO"
        )
        self.lesson_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create_pdf_with_json(
        self, filename: str, title: str, content: bytes
    ) -> tuple[Path, Path, bytes]:
        pdf = self.lesson_dir / filename
        pdf.write_bytes(content)
        sidecar = pdf.with_suffix(".json")
        data = {
            "hash_pdf": normalizer.sha256_file(pdf),
            "tema": title,
            "fonte_extracao": "pdf",
            "fonte_principal": "pdf",
            "arquivo_fonte_extracao": str(pdf),
            "arquivo_fonte": str(pdf),
            "caminho_pdf": str(pdf),
        }
        sidecar.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return pdf, sidecar, sidecar.read_bytes()

    def create_manifest(
        self, records: list[dict[str, object]], summary: dict[str, object]
    ) -> Path:
        output = self.base / "manifesto"
        return normalizer.write_manifest(output, self.root, records, summary)

    def test_rejeita_aula_dupla_e_remove_metadado_visual_do_titulo(self) -> None:
        lesson, reason = normalizer.parse_lesson_from_name("AULA_1_E_2")
        self.assertEqual(lesson, 1)
        self.assertIn("aulas 1 e 2", reason)
        self.assertEqual(
            normalizer.clean_extracted_title(
                "Efeito estufa: manutenção da vida Ensino Médio"
            ),
            "EFEITO_ESTUFA_MANUTENCAO_DA_VIDA",
        )
        self.assertFalse(normalizer.title_is_usable("3º bimestre"))
        self.assertFalse(normalizer.title_is_usable("Premissas de leitura 5"))
        self.assertFalse(normalizer.title_is_usable("Componente"))
        self.assertFalse(
            normalizer.title_is_usable(
                "GPS Guia de Práticas de Sala de Aula Práticas de Linguagem"
            )
        )

        math_title, math_source, _ = normalizer.extract_title_from_lines(
            [
                "2º bimestre",
                "Aula 20",
                "Ensino Médio",
                "Matemática",
                "Aula Khan",
                "Revisão: Equações logarítmicas -",
                "problemas",
                "Resolução de problemas",
                "relacionados a funções logarítmicas.",
            ],
            "MATEMATICA",
            20,
        )
        self.assertEqual(math_title, "REVISAO_EQUACOES_LOGARITMICAS_PROBLEMAS")
        self.assertEqual(math_source, "pdf_after_discipline")

        geography_title, geography_source, _ = normalizer.extract_title_from_lines(
            [
                "Urbanização mundial: evolução e",
                "redes urbanas",
                "3ª Série – Ensino Médio",
                "Aprofundamento em Geografia",
                "Aula 1",
                "3º Bimestre",
                "Mapa do",
                "componente",
            ],
            "APROFUNDAMENTO_EM_GEOGRAFIA",
            1,
        )
        self.assertEqual(
            geography_title, "URBANIZACAO_MUNDIAL_EVOLUCAO_E_REDES_URBANAS"
        )
        self.assertEqual(geography_source, "pdf_before_context")

    def test_aplica_valida_e_reverte_pdf_com_json(self) -> None:
        pdf, sidecar, original_json = self.create_pdf_with_json(
            "AULA1.pdf", "Células HeLa", b"pdf-ficticio-1"
        )
        records, summary = normalizer.plan_records(
            self.root, extract_pdf_titles=False
        )
        self.assertEqual(records[0]["status"], "ready_json")
        manifest = self.create_manifest(records, summary)
        target_pdf = normalizer.safe_path(self.root, records[0]["target_pdf"])
        target_json = target_pdf.with_suffix(".json")

        result = normalizer.apply_records(
            manifest, normalizer.PHASE_ONE_STATUSES, "alta_confianca"
        )

        self.assertEqual(result["count"], 1)
        self.assertFalse(pdf.exists())
        self.assertFalse(sidecar.exists())
        self.assertTrue(target_pdf.is_file())
        self.assertTrue(target_json.is_file())
        updated = normalizer.load_json(target_json)
        self.assertEqual(updated["arquivo_fonte"], str(target_pdf))
        self.assertTrue(normalizer.validate_manifest(manifest)["ok"])

        rollback = normalizer.rollback_manifest(manifest)

        self.assertEqual(rollback["count"], 1)
        self.assertTrue(pdf.is_file())
        self.assertTrue(sidecar.is_file())
        self.assertFalse(target_pdf.exists())
        self.assertFalse(target_json.exists())
        self.assertEqual(sidecar.read_bytes(), original_json)

    def test_falha_apos_mover_json_reverte_operacao_atual(self) -> None:
        pdf, sidecar, original_json = self.create_pdf_with_json(
            "AULA2.pdf", "Divisão celular", b"pdf-ficticio-2"
        )
        records, summary = normalizer.plan_records(
            self.root, extract_pdf_titles=False
        )
        manifest = self.create_manifest(records, summary)
        target_pdf = normalizer.safe_path(self.root, records[0]["target_pdf"])
        target_json = target_pdf.with_suffix(".json")

        with mock.patch.object(
            normalizer,
            "update_sidecar_paths",
            side_effect=RuntimeError("falha simulada"),
        ):
            with self.assertRaises(RuntimeError):
                normalizer.apply_records(
                    manifest,
                    normalizer.PHASE_ONE_STATUSES,
                    "alta_confianca",
                )

        self.assertTrue(pdf.is_file())
        self.assertTrue(sidecar.is_file())
        self.assertFalse(target_pdf.exists())
        self.assertFalse(target_json.exists())
        self.assertEqual(sidecar.read_bytes(), original_json)
        report = normalizer.load_apply_report(manifest.parent)
        self.assertEqual(report["operations"], [])
        self.assertEqual(report["phases"][-1]["state"], "rolled_back")

    def test_falha_na_segunda_fase_preserva_historico_da_primeira(self) -> None:
        first_pdf, _, _ = self.create_pdf_with_json(
            "AULA3_PRIMEIRO_TEMA.pdf", "Primeiro tema", b"pdf-ficticio-3"
        )
        second_pdf, second_json, second_json_bytes = self.create_pdf_with_json(
            "AULA4_SEGUNDO_TEMA.pdf", "Segundo tema", b"pdf-ficticio-4"
        )
        records, summary = normalizer.plan_records(
            self.root, extract_pdf_titles=False
        )
        second_record = next(
            record for record in records if record["source_name"].startswith("AULA4")
        )
        second_record["status"] = "ready_pdf_text"
        second_record["title_source"] = "pdf_direct"
        summary["status_counts"] = {
            "ready_filename": 1,
            "ready_pdf_text": 1,
        }
        manifest = self.create_manifest(records, summary)

        normalizer.apply_records(
            manifest, normalizer.PHASE_ONE_STATUSES, "alta_confianca"
        )
        first_record = next(
            record for record in records if record["source_name"].startswith("AULA3")
        )
        first_target = normalizer.safe_path(self.root, first_record["target_pdf"])
        second_target = normalizer.safe_path(
            self.root, second_record["target_pdf"]
        )

        with mock.patch.object(
            normalizer,
            "update_sidecar_paths",
            side_effect=RuntimeError("falha simulada na fase 2"),
        ):
            with self.assertRaises(RuntimeError):
                normalizer.apply_records(
                    manifest,
                    normalizer.PHASE_TWO_STATUSES,
                    "titulos_extraidos",
                )

        report = normalizer.load_apply_report(manifest.parent)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["source_pdf"], first_record["source_pdf"])
        self.assertTrue(first_target.is_file())
        self.assertFalse(first_pdf.exists())
        self.assertTrue(second_pdf.is_file())
        self.assertTrue(second_json.is_file())
        self.assertEqual(second_json.read_bytes(), second_json_bytes)
        self.assertFalse(second_target.exists())

        normalizer.rollback_manifest(manifest)
        self.assertTrue(first_pdf.is_file())


if __name__ == "__main__":
    unittest.main()
