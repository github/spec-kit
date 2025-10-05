import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_DescribeActiveReceiptRuleSetCommand, se_DescribeActiveReceiptRuleSetCommand } from "../protocols/Aws_query";
export { $Command };
export class DescribeActiveReceiptRuleSetCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "DescribeActiveReceiptRuleSet", {})
    .n("SESClient", "DescribeActiveReceiptRuleSetCommand")
    .f(void 0, void 0)
    .ser(se_DescribeActiveReceiptRuleSetCommand)
    .de(de_DescribeActiveReceiptRuleSetCommand)
    .build() {
}
