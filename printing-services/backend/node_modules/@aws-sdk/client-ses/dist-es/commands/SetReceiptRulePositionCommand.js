import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_SetReceiptRulePositionCommand, se_SetReceiptRulePositionCommand } from "../protocols/Aws_query";
export { $Command };
export class SetReceiptRulePositionCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "SetReceiptRulePosition", {})
    .n("SESClient", "SetReceiptRulePositionCommand")
    .f(void 0, void 0)
    .ser(se_SetReceiptRulePositionCommand)
    .de(de_SetReceiptRulePositionCommand)
    .build() {
}
