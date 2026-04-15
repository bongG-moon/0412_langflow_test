import unittest

from manufacturing_agent.app.ui_renderer import should_show_retry_question_guidance
from manufacturing_agent.shared.text_sanitizer import sanitize_markdown_text


class UiSanitizerStep7Tests(unittest.TestCase):
    def test_single_tilde_ranges_are_escaped_for_markdown(self):
        sanitized = sanitize_markdown_text("나머지 D/A3~D/A5 공정은 70~80%대입니다.")

        self.assertEqual(sanitized, "나머지 D/A3\\~D/A5 공정은 70\\~80%대입니다.")

    def test_normal_answer_does_not_show_retry_guidance(self):
        response = (
            "오늘(2026-04-15) DDR5 제품의 DA 세부 공정별 생산 달성율을 분석한 결과입니다. "
            "현재 결과 표에는 제품명과 날짜 컬럼이 생략되어 있으나, 이는 조회 범위 설정 단계에서 이미 필터링되어 산출된 결과입니다."
        )

        self.assertFalse(
            should_show_retry_question_guidance(
                response_text=response,
                failure_type="",
            )
        )

    def test_failure_signals_still_show_retry_guidance(self):
        self.assertTrue(
            should_show_retry_question_guidance(
                response_text="날짜를 적어주세요. 다시 질문해주세요.",
                failure_type="missing_date",
            )
        )

        self.assertTrue(
            should_show_retry_question_guidance(
                response_text="병합에 실패했습니다.",
                failure_type="",
            )
        )


if __name__ == "__main__":
    unittest.main()
