import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ListVerifiedEmailAddressesCommand, se_ListVerifiedEmailAddressesCommand } from "../protocols/Aws_query";
export { $Command };
export class ListVerifiedEmailAddressesCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "ListVerifiedEmailAddresses", {})
    .n("SESClient", "ListVerifiedEmailAddressesCommand")
    .f(void 0, void 0)
    .ser(se_ListVerifiedEmailAddressesCommand)
    .de(de_ListVerifiedEmailAddressesCommand)
    .build() {
}
