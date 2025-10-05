import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_GetIdentityMailFromDomainAttributesCommand, se_GetIdentityMailFromDomainAttributesCommand, } from "../protocols/Aws_query";
export { $Command };
export class GetIdentityMailFromDomainAttributesCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "GetIdentityMailFromDomainAttributes", {})
    .n("SESClient", "GetIdentityMailFromDomainAttributesCommand")
    .f(void 0, void 0)
    .ser(se_GetIdentityMailFromDomainAttributesCommand)
    .de(de_GetIdentityMailFromDomainAttributesCommand)
    .build() {
}
