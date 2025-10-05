import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_CloneReceiptRuleSetCommand, se_CloneReceiptRuleSetCommand } from "../protocols/Aws_query";
export { $Command };
export class CloneReceiptRuleSetCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "CloneReceiptRuleSet", {})
    .n("SESClient", "CloneReceiptRuleSetCommand")
    .f(void 0, void 0)
    .ser(se_CloneReceiptRuleSetCommand)
    .de(de_CloneReceiptRuleSetCommand)
    .build() {
}
