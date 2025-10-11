import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_GetSendQuotaCommand, se_GetSendQuotaCommand } from "../protocols/Aws_query";
export { $Command };
export class GetSendQuotaCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "GetSendQuota", {})
    .n("SESClient", "GetSendQuotaCommand")
    .f(void 0, void 0)
    .ser(se_GetSendQuotaCommand)
    .de(de_GetSendQuotaCommand)
    .build() {
}
