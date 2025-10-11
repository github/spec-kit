import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_GetSendStatisticsCommand, se_GetSendStatisticsCommand } from "../protocols/Aws_query";
export { $Command };
export class GetSendStatisticsCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "GetSendStatistics", {})
    .n("SESClient", "GetSendStatisticsCommand")
    .f(void 0, void 0)
    .ser(se_GetSendStatisticsCommand)
    .de(de_GetSendStatisticsCommand)
    .build() {
}
