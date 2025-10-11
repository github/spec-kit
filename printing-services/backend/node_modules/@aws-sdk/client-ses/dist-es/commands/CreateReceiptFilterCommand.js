import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_CreateReceiptFilterCommand, se_CreateReceiptFilterCommand } from "../protocols/Aws_query";
export { $Command };
export class CreateReceiptFilterCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "CreateReceiptFilter", {})
    .n("SESClient", "CreateReceiptFilterCommand")
    .f(void 0, void 0)
    .ser(se_CreateReceiptFilterCommand)
    .de(de_CreateReceiptFilterCommand)
    .build() {
}
