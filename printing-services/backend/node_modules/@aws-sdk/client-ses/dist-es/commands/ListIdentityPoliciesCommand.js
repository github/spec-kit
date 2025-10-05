import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_ListIdentityPoliciesCommand, se_ListIdentityPoliciesCommand } from "../protocols/Aws_query";
export { $Command };
export class ListIdentityPoliciesCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "ListIdentityPolicies", {})
    .n("SESClient", "ListIdentityPoliciesCommand")
    .f(void 0, void 0)
    .ser(se_ListIdentityPoliciesCommand)
    .de(de_ListIdentityPoliciesCommand)
    .build() {
}
