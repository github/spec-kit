import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_UpdateReceiptRuleCommand, se_UpdateReceiptRuleCommand } from "../protocols/Aws_query";
export { $Command };
export class UpdateReceiptRuleCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "UpdateReceiptRule", {})
    .n("SESClient", "UpdateReceiptRuleCommand")
    .f(void 0, void 0)
    .ser(se_UpdateReceiptRuleCommand)
    .de(de_UpdateReceiptRuleCommand)
    .build() {
}
