import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_GetIdentityVerificationAttributesCommand, se_GetIdentityVerificationAttributesCommand, } from "../protocols/Aws_query";
export { $Command };
export class GetIdentityVerificationAttributesCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "GetIdentityVerificationAttributes", {})
    .n("SESClient", "GetIdentityVerificationAttributesCommand")
    .f(void 0, void 0)
    .ser(se_GetIdentityVerificationAttributesCommand)
    .de(de_GetIdentityVerificationAttributesCommand)
    .build() {
}
