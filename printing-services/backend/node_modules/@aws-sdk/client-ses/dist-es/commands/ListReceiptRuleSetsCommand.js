import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ListReceiptRuleSetsCommand, se_ListReceiptRuleSetsCommand } from "../protocols/Aws_query";
export { $Command };
export class ListReceiptRuleSetsCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "ListReceiptRuleSets", {})
    .n("SESClient", "ListReceiptRuleSetsCommand")
    .f(void 0, void 0)
    .ser(se_ListReceiptRuleSetsCommand)
    .de(de_ListReceiptRuleSetsCommand)
    .build() {
}
