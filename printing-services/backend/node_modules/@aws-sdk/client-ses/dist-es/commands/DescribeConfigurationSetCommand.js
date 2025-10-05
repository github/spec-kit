import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DescribeConfigurationSetCommand, se_DescribeConfigurationSetCommand } from "../protocols/Aws_query";
export { $Command };
export class DescribeConfigurationSetCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "DescribeConfigurationSet", {})
    .n("SESClient", "DescribeConfigurationSetCommand")
    .f(void 0, void 0)
    .ser(se_DescribeConfigurationSetCommand)
    .de(de_DescribeConfigurationSetCommand)
    .build() {
}
