import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateAccountSendingEnabledRequest } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateAccountSendingEnabledCommand}.
 */
export interface UpdateAccountSendingEnabledCommandInput extends UpdateAccountSendingEnabledRequest {
}
/**
 * @public
 *
 * The output of {@link UpdateAccountSendingEnabledCommand}.
 */
export interface UpdateAccountSendingEnabledCommandOutput extends __MetadataBearer {
}
declare const UpdateAccountSendingEnabledCommand_base: {
    new (input: UpdateAccountSendingEnabledCommandInput): import("@smithy/smithy-client").CommandImpl<UpdateAccountSendingEnabledCommandInput, UpdateAccountSendingEnabledCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [UpdateAccountSendingEnabledCommandInput]): import("@smithy/smithy-client").CommandImpl<UpdateAccountSendingEnabledCommandInput, UpdateAccountSendingEnabledCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Enables or disables email sending across your entire Amazon SES account in the current
 *             Amazon Web Services Region. You can use this operation in conjunction with Amazon CloudWatch alarms to
 *             temporarily pause email sending across your Amazon SES account in a given Amazon Web Services Region when
 *             reputation metrics (such as your bounce or complaint rates) reach certain
 *             thresholds.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, UpdateAccountSendingEnabledCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, UpdateAccountSendingEnabledCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // UpdateAccountSendingEnabledRequest
 *   Enabled: true || false,
 * };
 * const command = new UpdateAccountSendingEnabledCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param UpdateAccountSendingEnabledCommandInput - {@link UpdateAccountSendingEnabledCommandInput}
 * @returns {@link UpdateAccountSendingEnabledCommandOutput}
 * @see {@link UpdateAccountSendingEnabledCommandInput} for command's `input` shape.
 * @see {@link UpdateAccountSendingEnabledCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example UpdateAccountSendingEnabled
 * ```javascript
 * // The following example updated the sending status for this account.
 * const input = {
 *   Enabled: true
 * };
 * const command = new UpdateAccountSendingEnabledCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class UpdateAccountSendingEnabledCommand extends UpdateAccountSendingEnabledCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: UpdateAccountSendingEnabledRequest;
            output: {};
        };
        sdk: {
            input: UpdateAccountSendingEnabledCommandInput;
            output: UpdateAccountSendingEnabledCommandOutput;
        };
    };
}
