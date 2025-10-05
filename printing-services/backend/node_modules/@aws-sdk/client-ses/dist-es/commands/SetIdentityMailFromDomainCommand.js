import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_SetIdentityMailFromDomainCommand, se_SetIdentityMailFromDomainCommand } from "../protocols/Aws_query";
export { $Command };
export class SetIdentityMailFromDomainCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "SetIdentityMailFromDomain", {})
    .n("SESClient", "SetIdentityMailFromDomainCommand")
    .f(void 0, void 0)
    .ser(se_SetIdentityMailFromDomainCommand)
    .de(de_SetIdentityMailFromDomainCommand)
    .build() {
}
