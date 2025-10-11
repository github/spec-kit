import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_CreateReceiptRuleCommand, se_CreateReceiptRuleCommand } from "../protocols/Aws_query";
export { $Command };
export class CreateReceiptRuleCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "CreateReceiptRule", {})
    .n("SESClient", "CreateReceiptRuleCommand")
    .f(void 0, void 0)
    .ser(se_CreateReceiptRuleCommand)
    .de(de_CreateReceiptRuleCommand)
    .build() {
}
