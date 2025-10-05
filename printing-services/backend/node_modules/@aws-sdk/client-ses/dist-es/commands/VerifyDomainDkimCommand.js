import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_VerifyDomainDkimCommand, se_VerifyDomainDkimCommand } from "../protocols/Aws_query";
export { $Command };
export class VerifyDomainDkimCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "VerifyDomainDkim", {})
    .n("SESClient", "VerifyDomainDkimCommand")
    .f(void 0, void 0)
    .ser(se_VerifyDomainDkimCommand)
    .de(de_VerifyDomainDkimCommand)
    .build() {
}
