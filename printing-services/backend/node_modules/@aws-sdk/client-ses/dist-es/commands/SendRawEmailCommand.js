import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_SendRawEmailCommand, se_SendRawEmailCommand } from "../protocols/Aws_query";
export { $Command };
export class SendRawEmailCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "SendRawEmail", {})
    .n("SESClient", "SendRawEmailCommand")
    .f(void 0, void 0)
    .ser(se_SendRawEmailCommand)
    .de(de_SendRawEmailCommand)
    .build() {
}
