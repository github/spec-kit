import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DeleteReceiptFilterCommand, se_DeleteReceiptFilterCommand } from "../protocols/Aws_query";
export { $Command };
export class DeleteReceiptFilterCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "DeleteReceiptFilter", {})
    .n("SESClient", "DeleteReceiptFilterCommand")
    .f(void 0, void 0)
    .ser(se_DeleteReceiptFilterCommand)
    .de(de_DeleteReceiptFilterCommand)
    .build() {
}
