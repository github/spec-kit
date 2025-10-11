import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_SendBulkTemplatedEmailCommand, se_SendBulkTemplatedEmailCommand } from "../protocols/Aws_query";
export { $Command };
export class SendBulkTemplatedEmailCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "SendBulkTemplatedEmail", {})
    .n("SESClient", "SendBulkTemplatedEmailCommand")
    .f(void 0, void 0)
    .ser(se_SendBulkTemplatedEmailCommand)
    .de(de_SendBulkTemplatedEmailCommand)
    .build() {
}
