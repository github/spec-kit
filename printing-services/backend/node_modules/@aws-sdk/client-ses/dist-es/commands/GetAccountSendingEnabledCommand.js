import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_GetAccountSendingEnabledCommand, se_GetAccountSendingEnabledCommand } from "../protocols/Aws_query";
export { $Command };
export class GetAccountSendingEnabledCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "GetAccountSendingEnabled", {})
    .n("SESClient", "GetAccountSendingEnabledCommand")
    .f(void 0, void 0)
    .ser(se_GetAccountSendingEnabledCommand)
    .de(de_GetAccountSendingEnabledCommand)
    .build() {
}
