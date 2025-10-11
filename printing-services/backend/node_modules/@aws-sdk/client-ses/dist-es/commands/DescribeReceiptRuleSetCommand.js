import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DescribeReceiptRuleSetCommand, se_DescribeReceiptRuleSetCommand } from "../protocols/Aws_query";
export { $Command };
export class DescribeReceiptRuleSetCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "DescribeReceiptRuleSet", {})
    .n("SESClient", "DescribeReceiptRuleSetCommand")
    .f(void 0, void 0)
    .ser(se_DescribeReceiptRuleSetCommand)
    .de(de_DescribeReceiptRuleSetCommand)
    .build() {
}
