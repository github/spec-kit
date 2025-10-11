import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ListReceiptFiltersCommand, se_ListReceiptFiltersCommand } from "../protocols/Aws_query";
export { $Command };
export class ListReceiptFiltersCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "ListReceiptFilters", {})
    .n("SESClient", "ListReceiptFiltersCommand")
    .f(void 0, void 0)
    .ser(se_ListReceiptFiltersCommand)
    .de(de_ListReceiptFiltersCommand)
    .build() {
}
