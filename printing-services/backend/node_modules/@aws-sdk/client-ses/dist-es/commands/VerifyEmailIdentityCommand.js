import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_VerifyEmailIdentityCommand, se_VerifyEmailIdentityCommand } from "../protocols/Aws_query";
export { $Command };
export class VerifyEmailIdentityCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "VerifyEmailIdentity", {})
    .n("SESClient", "VerifyEmailIdentityCommand")
    .f(void 0, void 0)
    .ser(se_VerifyEmailIdentityCommand)
    .de(de_VerifyEmailIdentityCommand)
    .build() {
}
