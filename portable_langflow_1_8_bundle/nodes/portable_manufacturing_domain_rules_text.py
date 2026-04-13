"""Portable Langflow node: emit manufacturing domain rules as reusable system/prompt text."""

from __future__ import annotations

from lfx.custom.custom_component.component import Component
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.message import Message


DOMAIN_RULES_TEXT = """Manufacturing assistant operating rules

1. Treat process groups and aliases as canonical manufacturing filters.
- DP/D-P includes WET1, WET2, L/T1, L/T2, B/G1, B/G2, H/S1, H/S2, W/S1, W/S2, WSD1, WSD2, WEC1, WEC2, WLS1, WLS2, WVI, UV, C/C1.
- D/A includes D/A1~D/A6.
- W/B includes W/B1~W/B6.
- FCB includes FCB1, FCB2, FCB/H.
- P/C includes P/C1~P/C5.
- QCSPC includes QCSPC1~QCSPC4.
- SAT includes SAT1, SAT2.
- P/L includes PLH.

2. Treat product attribute groups as value-expansion dictionaries.
- MODE: DDR4, DDR5, LPDDR5.
- DEN: 256G, 512G, 1T.
- TECH: LC, FO, FC.
- PKG_TYPE1: FCBGA, LFBGA.
- PKG_TYPE2: ODP, 16DP, SDP.

3. Apply registered custom value groups before planning retrieval.
- process_name '\ud6c4\uacf5\uc815A' means D/A1 and D/A2.

4. Use dataset keyword mapping before choosing tools.
- production: \uc0dd\uc0b0, production, \uc2e4\uc801, \ud22c\uc785, input, \uc778\ud48b, \uc0dd\uc0b0\ub7c9
- target: \ubaa9\ud45c, target, \uacc4\ud68d, \ubaa9\ud45c\ub7c9
- defect: \ubd88\ub7c9, defect, \uacb0\ud568
- equipment: \uc124\ube44, \uac00\ub3d9\ub960, equipment, downtime
- wip: wip, \uc7ac\uacf5, \ub300\uae30
- yield: \uc218\uc728, yield, pass rate, \ud569\uaca9\ub960, \uc591\ud488\ub960
- hold: hold, \ud640\ub4dc, \ubcf4\ub958 lot, hold lot
- scrap: scrap, \uc2a4\ud06c\ub7a9, \ud3d0\uae30, loss cost, \uc190\uc2e4\ube44\uc6a9
- recipe: recipe, \ub808\uc2dc\ud53c, \uacf5\uc815 \uc870\uac74, \uc870\uac74\uac12, parameter, \ud30c\ub77c\ubbf8\ud130
- lot_trace: lot, lot trace, lot \uc774\ub825, \ucd94\uc801, traceability, \ub85c\ud2b8

5. Match custom analysis rules before generic aggregation.
- HOLD \uc774\uc0c1\uc5ec\ubd80: use wip dataset and flag status HOLD or REWORK as anomaly.
- \uc0dd\uc0b0 \ubaa9\ud45c \ucc28\uc774\uc728: use production + target and calculate (production - target) / target.
- \ud640\ub4dc \ubd80\ud558\uc9c0\uc218: use hold + production and calculate hold_qty / production.
- \uc591\ud488\ub960 means the yield dataset.

6. Default built-in metrics.
- achievement_rate: production / target
- yield_rate: yield_rate or pass_qty / tested_qty
- production_saturation_rate: production / wip_qty

7. Use manufacturing retrieval tools by dataset key.
- production -> get_production_data
- target -> get_target_data
- defect -> get_defect_rate
- equipment -> get_equipment_status
- wip -> get_wip_status
- yield -> get_yield_data
- hold -> get_hold_data
- scrap -> get_scrap_data
- recipe -> get_recipe_data
- lot_trace -> get_lot_trace_data

8. Preserve multi-turn context.
- If previous current_data exists and the user asks for grouping, top-N, average, sum, or comparison of "that result", treat it as follow-up analysis.
- If the user explicitly changes date, dataset, or filter scope, treat it as a fresh retrieval.
"""


class PortableManufacturingDomainRulesTextComponent(Component):
    display_name = "Portable Manufacturing Domain Rules Text"
    description = "Emit manufacturing domain rules as Message text for Prompt Template or LLM system-message input."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "FileText"
    name = "portable_manufacturing_domain_rules_text"

    outputs = [
        Output(name="rules_message", display_name="Rules Message", method="rules_message", types=["Message"], selected="Message"),
        Output(name="rules_data", display_name="Rules Data", method="rules_data", types=["Data"], selected="Data"),
    ]

    def rules_message(self) -> Message:
        self.status = "Domain rules text ready"
        return Message(text=DOMAIN_RULES_TEXT, data={"kind": "domain_rules_text"})

    def rules_data(self) -> Data:
        self.status = "Domain rules text ready"
        return Data(data={"domain_rules_text": DOMAIN_RULES_TEXT})
