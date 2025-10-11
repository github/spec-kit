import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ReorderReceiptRuleSetCommand, se_ReorderReceiptRuleSetCommand } from "../protocols/Aws_query";
export { $Command };
export class ReorderReceiptRuleSetCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "ReorderReceiptRuleSet", {})
    .n("SESClient", "ReorderReceiptRuleSetCommand")
    .f(void 0, void 0)
    .ser(se_ReorderReceiptRuleSetCommand)
    .de(de_ReorderReceiptRuleSetCommand)
    .build() {
}
