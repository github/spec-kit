import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { SendBulkTemplatedEmailRequest, SendBulkTemplatedEmailResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link SendBulkTemplatedEmailCommand}.
 */
export interface SendBulkTemplatedEmailCommandInput extends SendBulkTemplatedEmailRequest {
}
/**
 * @public
 *
 * The output of {@link SendBulkTemplatedEmailCommand}.
 */
export interface SendBulkTemplatedEmailCommandOutput extends SendBulkTemplatedEmailResponse, __MetadataBearer {
}
declare const SendBulkTemplatedEmailCommand_base: {
    new (input: SendBulkTemplatedEmailCommandInput): import("@smithy/smithy-client").CommandImpl<SendBulkTemplatedEmailCommandInput, SendBulkTemplatedEmailCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: SendBulkTemplatedEmailCommandInput): import("@smithy/smithy-client").CommandImpl<SendBulkTemplatedEmailCommandInput, SendBulkTemplatedEmailCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Composes an email message to multiple destinations. The message body is created using
 *             an email template.</p>
 *          <p>To send email using this operation, your call must meet the following
 *             requirements:</p>
 *          <ul>
 *             <li>
 *                <p>The call must refer to an existing email template. You can create email
 *                     templates using <a>CreateTemplate</a>.</p>
 *             </li>
 *             <li>
 *                <p>The message must be sent from a verified email address or domain.</p>
 *             </li>
 *             <li>
 *                <p>If your account is still in the Amazon SES sandbox, you may send only to verified
 *                     addresses or domains, or to email addresses associated with the Amazon SES Mailbox
 *                     Simulator. For more information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html">Verifying Email
 *                         Addresses and Domains</a> in the <i>Amazon SES Developer
 *                         Guide.</i>
 *                </p>
 *             </li>
 *             <li>
 *                <p>The maximum message size is 10 MB.</p>
 *             </li>
 *             <li>
 *                <p>Each <code>Destination</code> parameter must include at least one recipient
 *                     email address. The recipient address can be a To: address, a CC: address, or a
 *                     BCC: address. If a recipient email address is invalid (that is, it is not in the
 *                     format <i>UserName@[SubDomain.]Domain.TopLevelDomain</i>), the
 *                     entire message is rejected, even if the message contains other recipients that
 *                     are valid.</p>
 *             </li>
 *             <li>
 *                <p>The message may not include more than 50 recipients, across the To:, CC: and
 *                     BCC: fields. If you need to send an email message to a larger audience, you can
 *                     divide your recipient list into groups of 50 or fewer, and then call the
 *                         <code>SendBulkTemplatedEmail</code> operation several times to send the
 *                     message to each group.</p>
 *             </li>
 *             <li>
 *                <p>The number of destinations you can contact in a single call can be limited by
 *                     your account's maximum sending rate.</p>
 *             </li>
 *          </ul>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, SendBulkTemplatedEmailCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, SendBulkTemplatedEmailCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // SendBulkTemplatedEmailRequest
 *   Source: "STRING_VALUE", // required
 *   SourceArn: "STRING_VALUE",
 *   ReplyToAddresses: [ // AddressList
 *     "STRING_VALUE",
 *   ],
 *   ReturnPath: "STRING_VALUE",
 *   ReturnPathArn: "STRING_VALUE",
 *   ConfigurationSetName: "STRING_VALUE",
 *   DefaultTags: [ // MessageTagList
 *     { // MessageTag
 *       Name: "STRING_VALUE", // required
 *       Value: "STRING_VALUE", // required
 *     },
 *   ],
 *   Template: "STRING_VALUE", // required
 *   TemplateArn: "STRING_VALUE",
 *   DefaultTemplateData: "STRING_VALUE", // required
 *   Destinations: [ // BulkEmailDestinationList // required
 *     { // BulkEmailDestination
 *       Destination: { // Destination
 *         ToAddresses: [
 *           "STRING_VALUE",
 *         ],
 *         CcAddresses: [
 *           "STRING_VALUE",
 *         ],
 *         BccAddresses: [
 *           "STRING_VALUE",
 *         ],
 *       },
 *       ReplacementTags: [
 *         {
 *           Name: "STRING_VALUE", // required
 *           Value: "STRING_VALUE", // required
 *         },
 *       ],
 *       ReplacementTemplateData: "STRING_VALUE",
 *     },
 *   ],
 * };
 * const command = new SendBulkTemplatedEmailCommand(input);
 * const response = await client.send(command);
 * // { // SendBulkTemplatedEmailResponse
 * //   Status: [ // BulkEmailDestinationStatusList // required
 * //     { // BulkEmailDestinationStatus
 * //       Status: "Success" || "MessageRejected" || "MailFromDomainNotVerified" || "ConfigurationSetDoesNotExist" || "TemplateDoesNotExist" || "AccountSuspended" || "AccountThrottled" || "AccountDailyQuotaExceeded" || "InvalidSendingPoolName" || "AccountSendingPaused" || "ConfigurationSetSendingPaused" || "InvalidParameterValue" || "TransientFailure" || "Failed",
 * //       Error: "STRING_VALUE",
 * //       MessageId: "STRING_VALUE",
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param SendBulkTemplatedEmailCommandInput - {@link SendBulkTemplatedEmailCommandInput}
 * @returns {@link SendBulkTemplatedEmailCommandOutput}
 * @see {@link SendBulkTemplatedEmailCommandInput} for command's `input` shape.
 * @see {@link SendBulkTemplatedEmailCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link AccountSendingPausedException} (client fault)
 *  <p>Indicates that email sending is disabled for your entire Amazon SES account.</p>
 *          <p>You can enable or disable email sending for your Amazon SES account using <a>UpdateAccountSendingEnabled</a>.</p>
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link ConfigurationSetSendingPausedException} (client fault)
 *  <p>Indicates that email sending is disabled for the configuration set.</p>
 *          <p>You can enable or disable email sending for a configuration set using <a>UpdateConfigurationSetSendingEnabled</a>.</p>
 *
 * @throws {@link MailFromDomainNotVerifiedException} (client fault)
 *  <p> Indicates that the message could not be sent because Amazon SES could not read the MX
 *             record required to use the specified MAIL FROM domain. For information about editing the
 *             custom MAIL FROM domain settings for an identity, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/mail-from-edit.html">Amazon SES Developer
 *                 Guide</a>.</p>
 *
 * @throws {@link MessageRejected} (client fault)
 *  <p>Indicates that the action failed, and the message could not be sent. Check the error
 *             stack for more information about what caused the error.</p>
 *
 * @throws {@link TemplateDoesNotExistException} (client fault)
 *  <p>Indicates that the Template object you specified does not exist in your Amazon SES
 *             account.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class SendBulkTemplatedEmailCommand extends SendBulkTemplatedEmailCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: SendBulkTemplatedEmailRequest;
            output: SendBulkTemplatedEmailResponse;
        };
        sdk: {
            input: SendBulkTemplatedEmailCommandInput;
            output: SendBulkTemplatedEmailCommandOutput;
        };
    };
}
