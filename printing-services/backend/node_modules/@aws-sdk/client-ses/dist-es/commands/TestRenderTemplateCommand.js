import { getEndpointPlugin } from "@smithy/middleware-endpoint";
import { getSerdePlugin } from "@smithy/middleware-serde";
import { Command as $Command } from "@smithy/smithy-client";
import { commonParams } from "../endpoint/EndpointParameters";
import { de_TestRenderTemplateCommand, se_TestRenderTemplateCommand } from "../protocols/Aws_query";
export { $Command };
export class TestRenderTemplateCommand extends $Command
    .classBuilder()
    .ep(commonParams)
    .m(function (Command, cs, config, o) {
    return [
        getSerdePlugin(config, this.serialize, this.deserialize),
        getEndpointPlugin(config, Command.getEndpointParameterInstructions()),
    ];
})
    .s("SimpleEmailService", "TestRenderTemplate", {})
    .n("SESClient", "TestRenderTemplateCommand")
    .f(void 0, void 0)
    .ser(se_TestRenderTemplateCommand)
    .de(de_TestRenderTemplateCommand)
    .build() {
}
