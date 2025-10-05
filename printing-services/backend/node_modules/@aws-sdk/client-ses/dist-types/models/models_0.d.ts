import { ExceptionOptionType as __ExceptionOptionType } from "@smithy/smithy-client";
import { SESServiceException as __BaseException } from "./SESServiceException";
/**
 * <p>Indicates that email sending is disabled for your entire Amazon SES account.</p>
 *          <p>You can enable or disable email sending for your Amazon SES account using <a>UpdateAccountSendingEnabled</a>.</p>
 * @public
 */
export declare class AccountSendingPausedException extends __BaseException {
    readonly name: "AccountSendingPausedException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<AccountSendingPausedException, __BaseException>);
}
/**
 * <p>When included in a receipt rule, this action adds a header to the received
 *             email.</p>
 *          <p>For information about adding a header using a receipt rule, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-add-header.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface AddHeaderAction {
    /**
     * <p>The name of the header to add to the incoming message. The name must contain at least
     *             one character, and can contain up to 50 characters. It consists of alphanumeric (a–z,
     *             A–Z, 0–9) characters and dashes.</p>
     * @public
     */
    HeaderName: string | undefined;
    /**
     * <p>The content to include in the header. This value can contain up to 2048 characters. It
     *             can't contain newline (<code>\n</code>) or carriage return (<code>\r</code>)
     *             characters.</p>
     * @public
     */
    HeaderValue: string | undefined;
}
/**
 * <p>Indicates that a resource could not be created because of a naming conflict.</p>
 * @public
 */
export declare class AlreadyExistsException extends __BaseException {
    readonly name: "AlreadyExistsException";
    readonly $fault: "client";
    /**
     * <p>Indicates that a resource could not be created because the resource name already
     *             exists.</p>
     * @public
     */
    Name?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<AlreadyExistsException, __BaseException>);
}
/**
 * @public
 * @enum
 */
export declare const BehaviorOnMXFailure: {
    readonly RejectMessage: "RejectMessage";
    readonly UseDefaultValue: "UseDefaultValue";
};
/**
 * @public
 */
export type BehaviorOnMXFailure = (typeof BehaviorOnMXFailure)[keyof typeof BehaviorOnMXFailure];
/**
 * <p>Represents textual data, plus an optional character set specification.</p>
 *          <p>By default, the text must be 7-bit ASCII, due to the constraints of the SMTP protocol.
 *             If the text must contain any other characters, then you must also specify a character
 *             set. Examples include UTF-8, ISO-8859-1, and Shift_JIS.</p>
 * @public
 */
export interface Content {
    /**
     * <p>The textual data of the content.</p>
     * @public
     */
    Data: string | undefined;
    /**
     * <p>The character set of the content.</p>
     * @public
     */
    Charset?: string | undefined;
}
/**
 * <p>Represents the body of the message. You can specify text, HTML, or both. If you use
 *             both, then the message should display correctly in the widest variety of email
 *             clients.</p>
 * @public
 */
export interface Body {
    /**
     * <p>The content of the message, in text format. Use this for text-based email clients, or
     *             clients on high-latency networks (such as mobile devices).</p>
     * @public
     */
    Text?: Content | undefined;
    /**
     * <p>The content of the message, in HTML format. Use this for email clients that can
     *             process HTML. You can include clickable links, formatted text, and much more in an HTML
     *             message.</p>
     * @public
     */
    Html?: Content | undefined;
}
/**
 * <p>When included in a receipt rule, this action rejects the received email by returning a
 *             bounce response to the sender and, optionally, publishes a notification to Amazon Simple Notification Service
 *             (Amazon SNS).</p>
 *          <p>For information about sending a bounce message in response to a received email, see
 *             the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-bounce.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface BounceAction {
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic to notify when the bounce action is
     *             taken. You can find the ARN of a topic by using the <a href="https://docs.aws.amazon.com/sns/latest/api/API_ListTopics.html">ListTopics</a> operation in
     *             Amazon SNS.</p>
     *          <p>For more information about Amazon SNS topics, see the <a href="https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html">Amazon SNS Developer Guide</a>.</p>
     * @public
     */
    TopicArn?: string | undefined;
    /**
     * <p>The SMTP reply code, as defined by <a href="https://tools.ietf.org/html/rfc5321">RFC 5321</a>.</p>
     * @public
     */
    SmtpReplyCode: string | undefined;
    /**
     * <p>The SMTP enhanced status code, as defined by <a href="https://tools.ietf.org/html/rfc3463">RFC 3463</a>.</p>
     * @public
     */
    StatusCode?: string | undefined;
    /**
     * <p>Human-readable text to include in the bounce message.</p>
     * @public
     */
    Message: string | undefined;
    /**
     * <p>The email address of the sender of the bounced email. This is the address from which
     *             the bounce message is sent.</p>
     * @public
     */
    Sender: string | undefined;
}
/**
 * @public
 * @enum
 */
export declare const BounceType: {
    readonly ContentRejected: "ContentRejected";
    readonly DoesNotExist: "DoesNotExist";
    readonly ExceededQuota: "ExceededQuota";
    readonly MessageTooLarge: "MessageTooLarge";
    readonly TemporaryFailure: "TemporaryFailure";
    readonly Undefined: "Undefined";
};
/**
 * @public
 */
export type BounceType = (typeof BounceType)[keyof typeof BounceType];
/**
 * @public
 * @enum
 */
export declare const DsnAction: {
    readonly DELAYED: "delayed";
    readonly DELIVERED: "delivered";
    readonly EXPANDED: "expanded";
    readonly FAILED: "failed";
    readonly RELAYED: "relayed";
};
/**
 * @public
 */
export type DsnAction = (typeof DsnAction)[keyof typeof DsnAction];
/**
 * <p>Additional X-headers to include in the Delivery Status Notification (DSN) when an
 *             email that Amazon SES receives on your behalf bounces.</p>
 *          <p>For information about receiving email through Amazon SES, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface ExtensionField {
    /**
     * <p>The name of the header to add. Must be between 1 and 50 characters, inclusive, and
     *             consist of alphanumeric (a-z, A-Z, 0-9) characters and dashes only.</p>
     * @public
     */
    Name: string | undefined;
    /**
     * <p>The value of the header to add. Must contain 2048 characters or fewer, and must not
     *             contain newline characters ("\r" or "\n").</p>
     * @public
     */
    Value: string | undefined;
}
/**
 * <p>Recipient-related information to include in the Delivery Status Notification (DSN)
 *             when an email that Amazon SES receives on your behalf bounces.</p>
 *          <p>For information about receiving email through Amazon SES, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface RecipientDsnFields {
    /**
     * <p>The email address that the message was ultimately delivered to. This corresponds to
     *             the <code>Final-Recipient</code> in the DSN. If not specified,
     *                 <code>FinalRecipient</code> is set to the <code>Recipient</code> specified in the
     *                 <code>BouncedRecipientInfo</code> structure. Either <code>FinalRecipient</code> or
     *             the recipient in <code>BouncedRecipientInfo</code> must be a recipient of the original
     *             bounced message.</p>
     *          <note>
     *             <p>Do not prepend the <code>FinalRecipient</code> email address with <code>rfc
     *                     822;</code>, as described in <a href="https://tools.ietf.org/html/rfc3798">RFC 3798</a>.</p>
     *          </note>
     * @public
     */
    FinalRecipient?: string | undefined;
    /**
     * <p>The action performed by the reporting mail transfer agent (MTA) as a result of its
     *             attempt to deliver the message to the recipient address. This is required by <a href="https://tools.ietf.org/html/rfc3464">RFC 3464</a>.</p>
     * @public
     */
    Action: DsnAction | undefined;
    /**
     * <p>The MTA to which the remote MTA attempted to deliver the message, formatted as
     *             specified in <a href="https://tools.ietf.org/html/rfc3464">RFC 3464</a>
     *                 (<code>mta-name-type; mta-name</code>). This parameter typically applies only to
     *             propagating synchronous bounces.</p>
     * @public
     */
    RemoteMta?: string | undefined;
    /**
     * <p>The status code that indicates what went wrong. This is required by <a href="https://tools.ietf.org/html/rfc3464">RFC 3464</a>.</p>
     * @public
     */
    Status: string | undefined;
    /**
     * <p>An extended explanation of what went wrong; this is usually an SMTP response. See
     *                 <a href="https://tools.ietf.org/html/rfc3463">RFC 3463</a> for the correct
     *             formatting of this parameter.</p>
     * @public
     */
    DiagnosticCode?: string | undefined;
    /**
     * <p>The time the final delivery attempt was made, in <a href="https://www.ietf.org/rfc/rfc0822.txt">RFC 822</a> date-time format.</p>
     * @public
     */
    LastAttemptDate?: Date | undefined;
    /**
     * <p>Additional X-headers to include in the DSN.</p>
     * @public
     */
    ExtensionFields?: ExtensionField[] | undefined;
}
/**
 * <p>Recipient-related information to include in the Delivery Status Notification (DSN)
 *             when an email that Amazon SES receives on your behalf bounces.</p>
 *          <p>For information about receiving email through Amazon SES, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface BouncedRecipientInfo {
    /**
     * <p>The email address of the recipient of the bounced email.</p>
     * @public
     */
    Recipient: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to receive
     *             email for the recipient of the bounced email. For more information about sending
     *             authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    RecipientArn?: string | undefined;
    /**
     * <p>The reason for the bounce. You must provide either this parameter or
     *                 <code>RecipientDsnFields</code>.</p>
     * @public
     */
    BounceType?: BounceType | undefined;
    /**
     * <p>Recipient-related DSN fields, most of which would normally be filled in automatically
     *             when provided with a <code>BounceType</code>. You must provide either this parameter or
     *                 <code>BounceType</code>.</p>
     * @public
     */
    RecipientDsnFields?: RecipientDsnFields | undefined;
}
/**
 * <p>Represents the destination of the message, consisting of To:, CC:, and BCC:
 *             fields.</p>
 *          <note>
 *             <p>Amazon SES does not support the SMTPUTF8 extension, as described in <a href="https://tools.ietf.org/html/rfc6531">RFC6531</a>. For this reason, the
 *                 email address string must be 7-bit ASCII. If you want to send to or from email
 *                 addresses that contain Unicode characters in the domain part of an address, you must
 *                 encode the domain using Punycode. Punycode is not permitted in the local part of the
 *                 email address (the part before the @ sign) nor in the "friendly from" name. If you
 *                 want to use Unicode characters in the "friendly from" name, you must encode the
 *                 "friendly from" name using MIME encoded-word syntax, as described in <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Sending raw email
 *                     using the Amazon SES API</a>. For more information about Punycode, see <a href="http://tools.ietf.org/html/rfc3492">RFC 3492</a>.</p>
 *          </note>
 * @public
 */
export interface Destination {
    /**
     * <p>The recipients to place on the To: line of the message.</p>
     * @public
     */
    ToAddresses?: string[] | undefined;
    /**
     * <p>The recipients to place on the CC: line of the message.</p>
     * @public
     */
    CcAddresses?: string[] | undefined;
    /**
     * <p>The recipients to place on the BCC: line of the message.</p>
     * @public
     */
    BccAddresses?: string[] | undefined;
}
/**
 * <p>Contains the name and value of a tag that you can provide to <code>SendEmail</code> or
 *                 <code>SendRawEmail</code> to apply to an email.</p>
 *          <p>Message tags, which you use with configuration sets, enable you to publish email
 *             sending events. For information about using configuration sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface MessageTag {
    /**
     * <p>The name of the tag. The name must meet the following requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), or
     *                     dashes (-).</p>
     *             </li>
     *             <li>
     *                <p>Contain 256 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Name: string | undefined;
    /**
     * <p>The value of the tag. The value must meet the following requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), or
     *                     dashes (-).</p>
     *             </li>
     *             <li>
     *                <p>Contain 256 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Value: string | undefined;
}
/**
 * <p>An array that contains one or more Destinations, as well as the tags and replacement
 *             data associated with each of those Destinations.</p>
 * @public
 */
export interface BulkEmailDestination {
    /**
     * <p>Represents the destination of the message, consisting of To:, CC:, and BCC:
     *             fields.</p>
     *          <note>
     *             <p>Amazon SES does not support the SMTPUTF8 extension, as described in <a href="https://tools.ietf.org/html/rfc6531">RFC6531</a>. For this reason, the
     *                 email address string must be 7-bit ASCII. If you want to send to or from email
     *                 addresses that contain Unicode characters in the domain part of an address, you must
     *                 encode the domain using Punycode. Punycode is not permitted in the local part of the
     *                 email address (the part before the @ sign) nor in the "friendly from" name. If you
     *                 want to use Unicode characters in the "friendly from" name, you must encode the
     *                 "friendly from" name using MIME encoded-word syntax, as described in <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Sending raw email
     *                     using the Amazon SES API</a>. For more information about Punycode, see <a href="http://tools.ietf.org/html/rfc3492">RFC 3492</a>.</p>
     *          </note>
     * @public
     */
    Destination: Destination | undefined;
    /**
     * <p>A list of tags, in the form of name/value pairs, to apply to an email that you send
     *             using <code>SendBulkTemplatedEmail</code>. Tags correspond to characteristics of the
     *             email that you define, so that you can publish email sending events.</p>
     * @public
     */
    ReplacementTags?: MessageTag[] | undefined;
    /**
     * <p>A list of replacement values to apply to the template. This parameter is a JSON
     *             object, typically consisting of key-value pairs in which the keys correspond to
     *             replacement tags in the email template.</p>
     * @public
     */
    ReplacementTemplateData?: string | undefined;
}
/**
 * @public
 * @enum
 */
export declare const BulkEmailStatus: {
    readonly AccountDailyQuotaExceeded: "AccountDailyQuotaExceeded";
    readonly AccountSendingPaused: "AccountSendingPaused";
    readonly AccountSuspended: "AccountSuspended";
    readonly AccountThrottled: "AccountThrottled";
    readonly ConfigurationSetDoesNotExist: "ConfigurationSetDoesNotExist";
    readonly ConfigurationSetSendingPaused: "ConfigurationSetSendingPaused";
    readonly Failed: "Failed";
    readonly InvalidParameterValue: "InvalidParameterValue";
    readonly InvalidSendingPoolName: "InvalidSendingPoolName";
    readonly MailFromDomainNotVerified: "MailFromDomainNotVerified";
    readonly MessageRejected: "MessageRejected";
    readonly Success: "Success";
    readonly TemplateDoesNotExist: "TemplateDoesNotExist";
    readonly TransientFailure: "TransientFailure";
};
/**
 * @public
 */
export type BulkEmailStatus = (typeof BulkEmailStatus)[keyof typeof BulkEmailStatus];
/**
 * <p>An object that contains the response from the <code>SendBulkTemplatedEmail</code>
 *             operation.</p>
 * @public
 */
export interface BulkEmailDestinationStatus {
    /**
     * <p>The status of a message sent using the <code>SendBulkTemplatedEmail</code>
     *             operation.</p>
     *          <p>Possible values for this parameter include:</p>
     *          <ul>
     *             <li>
     *                <p>
     *                   <code>Success</code>: Amazon SES accepted the message, and attempts to deliver it
     *                     to the recipients.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>MessageRejected</code>: The message was rejected because it contained a
     *                     virus.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>MailFromDomainNotVerified</code>: The sender's email address or domain
     *                     was not verified.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>ConfigurationSetDoesNotExist</code>: The configuration set you specified
     *                     does not exist.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>TemplateDoesNotExist</code>: The template you specified does not
     *                     exist.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>AccountSuspended</code>: Your account has been shut down because of
     *                     issues related to your email sending practices.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>AccountThrottled</code>: The number of emails you can send has been
     *                     reduced because your account has exceeded its allocated sending limit.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>AccountDailyQuotaExceeded</code>: You have reached or exceeded the
     *                     maximum number of emails you can send from your account in a 24-hour
     *                     period.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>InvalidSendingPoolName</code>: The configuration set you specified
     *                     refers to an IP pool that does not exist.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>AccountSendingPaused</code>: Email sending for the Amazon SES account was
     *                     disabled using the <a>UpdateAccountSendingEnabled</a>
     *                     operation.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>ConfigurationSetSendingPaused</code>: Email sending for this
     *                     configuration set was disabled using the <a>UpdateConfigurationSetSendingEnabled</a> operation.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>InvalidParameterValue</code>: One or more of the parameters you
     *                     specified when calling this operation was invalid. See the error message for
     *                     additional information.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>TransientFailure</code>: Amazon SES was unable to process your request
     *                     because of a temporary issue.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>Failed</code>: Amazon SES was unable to process your request. See the error
     *                     message for additional information.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Status?: BulkEmailStatus | undefined;
    /**
     * <p>A description of an error that prevented a message being sent using the
     *                 <code>SendBulkTemplatedEmail</code> operation.</p>
     * @public
     */
    Error?: string | undefined;
    /**
     * <p>The unique message identifier returned from the <code>SendBulkTemplatedEmail</code>
     *             operation.</p>
     * @public
     */
    MessageId?: string | undefined;
}
/**
 * <p>Indicates that the delete operation could not be completed.</p>
 * @public
 */
export declare class CannotDeleteException extends __BaseException {
    readonly name: "CannotDeleteException";
    readonly $fault: "client";
    /**
     * <p>Indicates that a resource could not be deleted because no resource with the specified
     *             name exists.</p>
     * @public
     */
    Name?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<CannotDeleteException, __BaseException>);
}
/**
 * <p>Represents a request to create a receipt rule set by cloning an existing one. You use
 *             receipt rule sets to receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface CloneReceiptRuleSetRequest {
    /**
     * <p>The name of the rule set to create. The name must meet the following
     *             requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), or
     *                     dashes (-).</p>
     *             </li>
     *             <li>
     *                <p>Start and end with a letter or number.</p>
     *             </li>
     *             <li>
     *                <p>Contain 64 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    RuleSetName: string | undefined;
    /**
     * <p>The name of the rule set to clone.</p>
     * @public
     */
    OriginalRuleSetName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface CloneReceiptRuleSetResponse {
}
/**
 * <p>Indicates that a resource could not be created because of service limits. For a list
 *             of Amazon SES limits, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/limits.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export declare class LimitExceededException extends __BaseException {
    readonly name: "LimitExceededException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<LimitExceededException, __BaseException>);
}
/**
 * <p>Indicates that the provided receipt rule set does not exist.</p>
 * @public
 */
export declare class RuleSetDoesNotExistException extends __BaseException {
    readonly name: "RuleSetDoesNotExistException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the named receipt rule set does not exist.</p>
     * @public
     */
    Name?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<RuleSetDoesNotExistException, __BaseException>);
}
/**
 * @public
 * @enum
 */
export declare const DimensionValueSource: {
    readonly EMAIL_HEADER: "emailHeader";
    readonly LINK_TAG: "linkTag";
    readonly MESSAGE_TAG: "messageTag";
};
/**
 * @public
 */
export type DimensionValueSource = (typeof DimensionValueSource)[keyof typeof DimensionValueSource];
/**
 * <p>Contains the dimension configuration to use when you publish email sending events to
 *             Amazon CloudWatch.</p>
 *          <p>For information about publishing email sending events to Amazon CloudWatch, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface CloudWatchDimensionConfiguration {
    /**
     * <p>The name of an Amazon CloudWatch dimension associated with an email sending metric. The name
     *             must meet the following requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), dashes
     *                     (-), or colons (:).</p>
     *             </li>
     *             <li>
     *                <p>Contain 256 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    DimensionName: string | undefined;
    /**
     * <p>The place where Amazon SES finds the value of a dimension to publish to Amazon CloudWatch. To use
     *             the message tags that you specify using an <code>X-SES-MESSAGE-TAGS</code> header or a
     *             parameter to the <code>SendEmail</code>/<code>SendRawEmail</code> API, specify
     *                 <code>messageTag</code>. To use your own email headers, specify
     *                 <code>emailHeader</code>. To put a custom tag on any link included in your email,
     *             specify <code>linkTag</code>.</p>
     * @public
     */
    DimensionValueSource: DimensionValueSource | undefined;
    /**
     * <p>The default value of the dimension that is published to Amazon CloudWatch if you do not provide
     *             the value of the dimension when you send an email. The default value must meet the
     *             following requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), dashes
     *                     (-), at signs (@), or periods (.).</p>
     *             </li>
     *             <li>
     *                <p>Contain 256 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    DefaultDimensionValue: string | undefined;
}
/**
 * <p>Contains information associated with an Amazon CloudWatch event destination to which email
 *             sending events are published.</p>
 *          <p>Event destinations, such as Amazon CloudWatch, are associated with configuration sets, which
 *             enable you to publish email sending events. For information about using configuration
 *             sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface CloudWatchDestination {
    /**
     * <p>A list of dimensions upon which to categorize your emails when you publish email
     *             sending events to Amazon CloudWatch.</p>
     * @public
     */
    DimensionConfigurations: CloudWatchDimensionConfiguration[] | undefined;
}
/**
 * <p>The name of the configuration set.</p>
 *          <p>Configuration sets let you create groups of rules that you can apply to the emails you
 *             send using Amazon SES. For more information about using configuration sets, see <a href="https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html">Using Amazon SES
 *                 Configuration Sets</a> in the <a href="https://docs.aws.amazon.com/ses/latest/dg/">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface ConfigurationSet {
    /**
     * <p>The name of the configuration set. The name must meet the following
     *             requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only letters (a-z, A-Z), numbers (0-9), underscores (_), or dashes
     *                     (-).</p>
     *             </li>
     *             <li>
     *                <p>Contain 64 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Name: string | undefined;
}
/**
 * <p>Indicates that the configuration set could not be created because of a naming
 *             conflict.</p>
 * @public
 */
export declare class ConfigurationSetAlreadyExistsException extends __BaseException {
    readonly name: "ConfigurationSetAlreadyExistsException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the configuration set does not exist.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<ConfigurationSetAlreadyExistsException, __BaseException>);
}
/**
 * @public
 * @enum
 */
export declare const ConfigurationSetAttribute: {
    readonly DELIVERY_OPTIONS: "deliveryOptions";
    readonly EVENT_DESTINATIONS: "eventDestinations";
    readonly REPUTATION_OPTIONS: "reputationOptions";
    readonly TRACKING_OPTIONS: "trackingOptions";
};
/**
 * @public
 */
export type ConfigurationSetAttribute = (typeof ConfigurationSetAttribute)[keyof typeof ConfigurationSetAttribute];
/**
 * <p>Indicates that the configuration set does not exist.</p>
 * @public
 */
export declare class ConfigurationSetDoesNotExistException extends __BaseException {
    readonly name: "ConfigurationSetDoesNotExistException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the configuration set does not exist.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<ConfigurationSetDoesNotExistException, __BaseException>);
}
/**
 * <p>Indicates that email sending is disabled for the configuration set.</p>
 *          <p>You can enable or disable email sending for a configuration set using <a>UpdateConfigurationSetSendingEnabled</a>.</p>
 * @public
 */
export declare class ConfigurationSetSendingPausedException extends __BaseException {
    readonly name: "ConfigurationSetSendingPausedException";
    readonly $fault: "client";
    /**
     * <p>The name of the configuration set for which email sending is disabled.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<ConfigurationSetSendingPausedException, __BaseException>);
}
/**
 * <p>When included in a receipt rule, this action parses the received message and
 *             starts an email contact in Amazon Connect on your behalf.</p>
 *          <note>
 *             <p>When you receive emails, the maximum email size (including headers) is 40 MB.
 *                 Additionally, emails may only have up to 10 attachments.
 *                 Emails larger than 40 MB or with more than 10 attachments will be bounced.</p>
 *          </note>
 *          <p>We recommend that you configure this action via Amazon Connect.</p>
 * @public
 */
export interface ConnectAction {
    /**
     * <p>The Amazon Resource Name (ARN) for the Amazon Connect instance that Amazon SES integrates with for starting
     *             email contacts.</p>
     *          <p>For more information about Amazon Connect instances, see the <a href="https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-instances.html">Amazon Connect Administrator Guide</a>
     *          </p>
     * @public
     */
    InstanceARN: string | undefined;
    /**
     * <p> The Amazon Resource Name (ARN) of the IAM role to be used by Amazon Simple Email Service while starting email contacts
     *             to the Amazon Connect instance. This role should have permission to invoke <code>connect:StartEmailContact</code>
     *             for the given Amazon Connect instance.</p>
     * @public
     */
    IAMRoleARN: string | undefined;
}
/**
 * <p>Represents a request to create a configuration set. Configuration sets enable you to
 *             publish email sending events. For information about using configuration sets, see the
 *                 <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface CreateConfigurationSetRequest {
    /**
     * <p>A data structure that contains the name of the configuration set.</p>
     * @public
     */
    ConfigurationSet: ConfigurationSet | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface CreateConfigurationSetResponse {
}
/**
 * <p>Indicates that the configuration set is invalid. See the error message for
 *             details.</p>
 * @public
 */
export declare class InvalidConfigurationSetException extends __BaseException {
    readonly name: "InvalidConfigurationSetException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidConfigurationSetException, __BaseException>);
}
/**
 * <p>Contains the delivery stream ARN and the IAM role ARN associated with an Amazon Kinesis Firehose event
 *             destination.</p>
 *          <p>Event destinations, such as Amazon Kinesis Firehose, are associated with configuration sets, which enable
 *             you to publish email sending events. For information about using configuration sets, see
 *             the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface KinesisFirehoseDestination {
    /**
     * <p>The ARN of the IAM role under which Amazon SES publishes email sending events to the Amazon Kinesis Firehose
     *             stream.</p>
     * @public
     */
    IAMRoleARN: string | undefined;
    /**
     * <p>The ARN of the Amazon Kinesis Firehose stream that email sending events should be published to.</p>
     * @public
     */
    DeliveryStreamARN: string | undefined;
}
/**
 * @public
 * @enum
 */
export declare const EventType: {
    readonly BOUNCE: "bounce";
    readonly CLICK: "click";
    readonly COMPLAINT: "complaint";
    readonly DELIVERY: "delivery";
    readonly OPEN: "open";
    readonly REJECT: "reject";
    readonly RENDERING_FAILURE: "renderingFailure";
    readonly SEND: "send";
};
/**
 * @public
 */
export type EventType = (typeof EventType)[keyof typeof EventType];
/**
 * <p>Contains the topic ARN associated with an Amazon Simple Notification Service (Amazon SNS) event destination.</p>
 *          <p>Event destinations, such as Amazon SNS, are associated with configuration sets, which
 *             enable you to publish email sending events. For information about using configuration
 *             sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface SNSDestination {
    /**
     * <p>The ARN of the Amazon SNS topic for email sending events. You can find the ARN of a topic
     *             by using the <a href="https://docs.aws.amazon.com/sns/latest/api/API_ListTopics.html">ListTopics</a> Amazon SNS operation.</p>
     *          <p>For more information about Amazon SNS topics, see the <a href="https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html">Amazon SNS Developer Guide</a>.</p>
     * @public
     */
    TopicARN: string | undefined;
}
/**
 * <p>Contains information about an event destination.</p>
 *          <note>
 *             <p>When you create or update an event destination, you must provide one, and only
 *                 one, destination. The destination can be Amazon CloudWatch, Amazon Kinesis Firehose or Amazon Simple Notification Service (Amazon SNS).</p>
 *          </note>
 *          <p>Event destinations are associated with configuration sets, which enable you to publish
 *             email sending events to Amazon CloudWatch, Amazon Kinesis Firehose, or Amazon Simple Notification Service (Amazon SNS). For information about
 *             using configuration sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface EventDestination {
    /**
     * <p>The name of the event destination. The name must meet the following
     *             requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), or
     *                     dashes (-).</p>
     *             </li>
     *             <li>
     *                <p>Contain 64 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Name: string | undefined;
    /**
     * <p>Sets whether Amazon SES publishes events to this destination when you send an email with
     *             the associated configuration set. Set to <code>true</code> to enable publishing to this
     *             destination; set to <code>false</code> to prevent publishing to this destination. The
     *             default value is <code>false</code>.</p>
     * @public
     */
    Enabled?: boolean | undefined;
    /**
     * <p>The type of email sending events to publish to the event destination.</p>
     *          <ul>
     *             <li>
     *                <p>
     *                   <code>send</code> - The call was successful and Amazon SES is attempting to deliver
     *                     the email.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>reject</code> - Amazon SES determined that the email contained a virus and
     *                     rejected it.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>bounce</code> - The recipient's mail server permanently rejected the
     *                     email. This corresponds to a hard bounce.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>complaint</code> - The recipient marked the email as spam.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>delivery</code> - Amazon SES successfully delivered the email to the
     *                     recipient's mail server.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>open</code> - The recipient received the email and opened it in their
     *                     email client.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>click</code> - The recipient clicked one or more links in the
     *                     email.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>renderingFailure</code> - Amazon SES did not send the email because of a
     *                     template rendering issue.</p>
     *             </li>
     *          </ul>
     * @public
     */
    MatchingEventTypes: EventType[] | undefined;
    /**
     * <p>An object that contains the delivery stream ARN and the IAM role ARN associated with
     *             an Amazon Kinesis Firehose event destination.</p>
     * @public
     */
    KinesisFirehoseDestination?: KinesisFirehoseDestination | undefined;
    /**
     * <p>An object that contains the names, default values, and sources of the dimensions
     *             associated with an Amazon CloudWatch event destination.</p>
     * @public
     */
    CloudWatchDestination?: CloudWatchDestination | undefined;
    /**
     * <p>An object that contains the topic ARN associated with an Amazon Simple Notification Service (Amazon SNS) event
     *             destination.</p>
     * @public
     */
    SNSDestination?: SNSDestination | undefined;
}
/**
 * <p>Represents a request to create a configuration set event destination. A configuration
 *             set event destination, which can be either Amazon CloudWatch or Amazon Kinesis Firehose, describes an Amazon Web Services service
 *             in which Amazon SES publishes the email sending events associated with a configuration set.
 *             For information about using configuration sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface CreateConfigurationSetEventDestinationRequest {
    /**
     * <p>The name of the configuration set that the event destination should be associated
     *             with.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>An object that describes the Amazon Web Services service that email sending event where information
     *             is published.</p>
     * @public
     */
    EventDestination: EventDestination | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface CreateConfigurationSetEventDestinationResponse {
}
/**
 * <p>Indicates that the event destination could not be created because of a naming
 *             conflict.</p>
 * @public
 */
export declare class EventDestinationAlreadyExistsException extends __BaseException {
    readonly name: "EventDestinationAlreadyExistsException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the configuration set does not exist.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * <p>Indicates that the event destination does not exist.</p>
     * @public
     */
    EventDestinationName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<EventDestinationAlreadyExistsException, __BaseException>);
}
/**
 * <p>Indicates that the Amazon CloudWatch destination is invalid. See the error message for
 *             details.</p>
 * @public
 */
export declare class InvalidCloudWatchDestinationException extends __BaseException {
    readonly name: "InvalidCloudWatchDestinationException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the configuration set does not exist.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * <p>Indicates that the event destination does not exist.</p>
     * @public
     */
    EventDestinationName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidCloudWatchDestinationException, __BaseException>);
}
/**
 * <p>Indicates that the Amazon Kinesis Firehose destination is invalid. See the error
 *             message for details.</p>
 * @public
 */
export declare class InvalidFirehoseDestinationException extends __BaseException {
    readonly name: "InvalidFirehoseDestinationException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the configuration set does not exist.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * <p>Indicates that the event destination does not exist.</p>
     * @public
     */
    EventDestinationName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidFirehoseDestinationException, __BaseException>);
}
/**
 * <p>Indicates that the Amazon Simple Notification Service (Amazon SNS) destination is
 *             invalid. See the error message for details.</p>
 * @public
 */
export declare class InvalidSNSDestinationException extends __BaseException {
    readonly name: "InvalidSNSDestinationException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the configuration set does not exist.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * <p>Indicates that the event destination does not exist.</p>
     * @public
     */
    EventDestinationName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidSNSDestinationException, __BaseException>);
}
/**
 * <p>A domain that is used to redirect email recipients to an Amazon SES-operated domain. This
 *             domain captures open and click events generated by Amazon SES emails.</p>
 *          <p>For more information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/configure-custom-open-click-domains.html">Configuring Custom
 *                 Domains to Handle Open and Click Tracking</a> in the <i>Amazon SES Developer
 *                 Guide</i>.</p>
 * @public
 */
export interface TrackingOptions {
    /**
     * <p>The custom subdomain that is used to redirect email recipients to the Amazon SES event
     *             tracking domain.</p>
     * @public
     */
    CustomRedirectDomain?: string | undefined;
}
/**
 * <p>Represents a request to create an open and click tracking option object in a
 *             configuration set. </p>
 * @public
 */
export interface CreateConfigurationSetTrackingOptionsRequest {
    /**
     * <p>The name of the configuration set that the tracking options should be associated
     *             with.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>A domain that is used to redirect email recipients to an Amazon SES-operated domain. This
     *             domain captures open and click events generated by Amazon SES emails.</p>
     *          <p>For more information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/configure-custom-open-click-domains.html">Configuring Custom
     *                 Domains to Handle Open and Click Tracking</a> in the <i>Amazon SES Developer
     *                 Guide</i>.</p>
     * @public
     */
    TrackingOptions: TrackingOptions | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface CreateConfigurationSetTrackingOptionsResponse {
}
/**
 * <p>Indicates that the custom domain to be used for open and click tracking redirects is
 *             invalid. This error appears most often in the following situations:</p>
 *          <ul>
 *             <li>
 *                <p>When the tracking domain you specified is not verified in Amazon SES.</p>
 *             </li>
 *             <li>
 *                <p>When the tracking domain you specified is not a valid domain or
 *                     subdomain.</p>
 *             </li>
 *          </ul>
 * @public
 */
export declare class InvalidTrackingOptionsException extends __BaseException {
    readonly name: "InvalidTrackingOptionsException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidTrackingOptionsException, __BaseException>);
}
/**
 * <p>Indicates that the configuration set you specified already contains a TrackingOptions
 *             object.</p>
 * @public
 */
export declare class TrackingOptionsAlreadyExistsException extends __BaseException {
    readonly name: "TrackingOptionsAlreadyExistsException";
    readonly $fault: "client";
    /**
     * <p>Indicates that a TrackingOptions object already exists in the specified configuration
     *             set.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<TrackingOptionsAlreadyExistsException, __BaseException>);
}
/**
 * <p>Represents a request to create a custom verification email template.</p>
 * @public
 */
export interface CreateCustomVerificationEmailTemplateRequest {
    /**
     * <p>The name of the custom verification email template.</p>
     * @public
     */
    TemplateName: string | undefined;
    /**
     * <p>The email address that the custom verification email is sent from.</p>
     * @public
     */
    FromEmailAddress: string | undefined;
    /**
     * <p>The subject line of the custom verification email.</p>
     * @public
     */
    TemplateSubject: string | undefined;
    /**
     * <p>The content of the custom verification email. The total size of the email must be less
     *             than 10 MB. The message body may contain HTML, with some limitations. For more
     *             information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#send-email-verify-address-custom">Custom
     *                 Verification Email Frequently Asked Questions</a> in the <i>Amazon SES
     *                 Developer Guide</i>.</p>
     * @public
     */
    TemplateContent: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is successfully verified.</p>
     * @public
     */
    SuccessRedirectionURL: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is not successfully verified.</p>
     * @public
     */
    FailureRedirectionURL: string | undefined;
}
/**
 * <p>Indicates that custom verification email template provided content is invalid.</p>
 * @public
 */
export declare class CustomVerificationEmailInvalidContentException extends __BaseException {
    readonly name: "CustomVerificationEmailInvalidContentException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<CustomVerificationEmailInvalidContentException, __BaseException>);
}
/**
 * <p>Indicates that a custom verification email template with the name you specified
 *             already exists.</p>
 * @public
 */
export declare class CustomVerificationEmailTemplateAlreadyExistsException extends __BaseException {
    readonly name: "CustomVerificationEmailTemplateAlreadyExistsException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the provided custom verification email template with the specified
     *             template name already exists.</p>
     * @public
     */
    CustomVerificationEmailTemplateName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<CustomVerificationEmailTemplateAlreadyExistsException, __BaseException>);
}
/**
 * <p>Indicates that the sender address specified for a custom verification email is not
 *             verified, and is therefore not eligible to send the custom verification email. </p>
 * @public
 */
export declare class FromEmailAddressNotVerifiedException extends __BaseException {
    readonly name: "FromEmailAddressNotVerifiedException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the from email address associated with the custom verification email
     *             template is not verified.</p>
     * @public
     */
    FromEmailAddress?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<FromEmailAddressNotVerifiedException, __BaseException>);
}
/**
 * @public
 * @enum
 */
export declare const ReceiptFilterPolicy: {
    readonly Allow: "Allow";
    readonly Block: "Block";
};
/**
 * @public
 */
export type ReceiptFilterPolicy = (typeof ReceiptFilterPolicy)[keyof typeof ReceiptFilterPolicy];
/**
 * <p>A receipt IP address filter enables you to specify whether to accept or reject mail
 *             originating from an IP address or range of IP addresses.</p>
 *          <p>For information about setting up IP address filters, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-ip-filtering-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface ReceiptIpFilter {
    /**
     * <p>Indicates whether to block or allow incoming mail from the specified IP
     *             addresses.</p>
     * @public
     */
    Policy: ReceiptFilterPolicy | undefined;
    /**
     * <p>A single IP address or a range of IP addresses to block or allow, specified in
     *             Classless Inter-Domain Routing (CIDR) notation. An example of a single email address is
     *             10.0.0.1. An example of a range of IP addresses is 10.0.0.1/24. For more information
     *             about CIDR notation, see <a href="https://tools.ietf.org/html/rfc2317">RFC
     *                 2317</a>.</p>
     * @public
     */
    Cidr: string | undefined;
}
/**
 * <p>A receipt IP address filter enables you to specify whether to accept or reject mail
 *             originating from an IP address or range of IP addresses.</p>
 *          <p>For information about setting up IP address filters, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-ip-filtering-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface ReceiptFilter {
    /**
     * <p>The name of the IP address filter. The name must meet the following
     *             requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), or
     *                     dashes (-).</p>
     *             </li>
     *             <li>
     *                <p>Start and end with a letter or number.</p>
     *             </li>
     *             <li>
     *                <p>Contain 64 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Name: string | undefined;
    /**
     * <p>A structure that provides the IP addresses to block or allow, and whether to block or
     *             allow incoming mail from them.</p>
     * @public
     */
    IpFilter: ReceiptIpFilter | undefined;
}
/**
 * <p>Represents a request to create a new IP address filter. You use IP address filters
 *             when you receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface CreateReceiptFilterRequest {
    /**
     * <p>A data structure that describes the IP address filter to create, which consists of a
     *             name, an IP address range, and whether to allow or block mail from it.</p>
     * @public
     */
    Filter: ReceiptFilter | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface CreateReceiptFilterResponse {
}
/**
 * @public
 * @enum
 */
export declare const InvocationType: {
    readonly Event: "Event";
    readonly RequestResponse: "RequestResponse";
};
/**
 * @public
 */
export type InvocationType = (typeof InvocationType)[keyof typeof InvocationType];
/**
 * <p>When included in a receipt rule, this action calls an Amazon Web Services Lambda function and,
 *             optionally, publishes a notification to Amazon Simple Notification Service (Amazon SNS).</p>
 *          <p>To enable Amazon SES to call your Amazon Web Services Lambda function or to publish to an Amazon SNS topic of
 *             another account, Amazon SES must have permission to access those resources. For information
 *             about giving permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-permissions.html">Amazon SES Developer
 *             Guide</a>.</p>
 *          <p>For information about using Amazon Web Services Lambda actions in receipt rules, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-lambda.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface LambdaAction {
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic to notify when the Lambda action is
     *             executed. You can find the ARN of a topic by using the <a href="https://docs.aws.amazon.com/sns/latest/api/API_ListTopics.html">ListTopics</a> operation in
     *             Amazon SNS.</p>
     *          <p>For more information about Amazon SNS topics, see the <a href="https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html">Amazon SNS Developer Guide</a>.</p>
     * @public
     */
    TopicArn?: string | undefined;
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon Web Services Lambda function. An example of an Amazon Web Services Lambda
     *             function ARN is <code>arn:aws:lambda:us-west-2:account-id:function:MyFunction</code>.
     *             For more information about Amazon Web Services Lambda, see the <a href="https://docs.aws.amazon.com/lambda/latest/dg/welcome.html">Amazon Web Services Lambda Developer Guide</a>.</p>
     * @public
     */
    FunctionArn: string | undefined;
    /**
     * <p>The invocation type of the Amazon Web Services Lambda function. An invocation type of
     *                 <code>RequestResponse</code> means that the execution of the function immediately
     *             results in a response, and a value of <code>Event</code> means that the function is
     *             invoked asynchronously. The default value is <code>Event</code>. For information about
     *             Amazon Web Services Lambda invocation types, see the <a href="https://docs.aws.amazon.com/lambda/latest/dg/API_Invoke.html">Amazon Web Services Lambda Developer Guide</a>.</p>
     *          <important>
     *             <p>There is a 30-second timeout on <code>RequestResponse</code> invocations. You
     *                 should use <code>Event</code> invocation in most cases. Use
     *                     <code>RequestResponse</code> only to make a mail flow decision, such as whether
     *                 to stop the receipt rule or the receipt rule set.</p>
     *          </important>
     * @public
     */
    InvocationType?: InvocationType | undefined;
}
/**
 * <p>When included in a receipt rule, this action saves the received message to an Amazon Simple Storage Service
 *             (Amazon S3) bucket and, optionally, publishes a notification to Amazon Simple Notification Service (Amazon SNS).</p>
 *          <p>To enable Amazon SES to write emails to your Amazon S3 bucket, use an Amazon Web Services KMS key to encrypt
 *             your emails, or publish to an Amazon SNS topic of another account, Amazon SES must have permission
 *             to access those resources. For information about granting permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-permissions.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <note>
 *             <p>When you save your emails to an Amazon S3 bucket, the maximum email size (including
 *                 headers) is 40 MB. Emails larger than that bounces.</p>
 *          </note>
 *          <p>For information about specifying Amazon S3 actions in receipt rules, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-s3.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface S3Action {
    /**
     * <p>The ARN of the Amazon SNS topic to notify when the message is saved to the Amazon S3 bucket. You
     *             can find the ARN of a topic by using the <a href="https://docs.aws.amazon.com/sns/latest/api/API_ListTopics.html">ListTopics</a> operation in
     *             Amazon SNS.</p>
     *          <p>For more information about Amazon SNS topics, see the <a href="https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html">Amazon SNS Developer Guide</a>.</p>
     * @public
     */
    TopicArn?: string | undefined;
    /**
     * <p>The name of the Amazon S3 bucket for incoming email.</p>
     * @public
     */
    BucketName: string | undefined;
    /**
     * <p>The key prefix of the Amazon S3 bucket. The key prefix is similar to a directory name that
     *             enables you to store similar data under the same directory in a bucket.</p>
     * @public
     */
    ObjectKeyPrefix?: string | undefined;
    /**
     * <p>The customer managed key that Amazon SES should use to encrypt your emails before saving
     *             them to the Amazon S3 bucket. You can use the Amazon Web Services managed key or a customer managed key
     *             that you created in Amazon Web Services KMS as follows:</p>
     *          <ul>
     *             <li>
     *                <p>To use the Amazon Web Services managed key, provide an ARN in the form of
     *                         <code>arn:aws:kms:REGION:ACCOUNT-ID-WITHOUT-HYPHENS:alias/aws/ses</code>.
     *                     For example, if your Amazon Web Services account ID is 123456789012 and you want to use the
     *                     Amazon Web Services managed key in the US West (Oregon) Region, the ARN of the Amazon Web Services managed
     *                     key would be <code>arn:aws:kms:us-west-2:123456789012:alias/aws/ses</code>. If
     *                     you use the Amazon Web Services managed key, you don't need to perform any extra steps to give
     *                     Amazon SES permission to use the key.</p>
     *             </li>
     *             <li>
     *                <p>To use a customer managed key that you created in Amazon Web Services KMS, provide the ARN
     *                     of the customer managed key and ensure that you add a statement to your key's
     *                     policy to give Amazon SES permission to use it. For more information about giving
     *                     permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-permissions.html">Amazon SES Developer
     *                         Guide</a>.</p>
     *             </li>
     *          </ul>
     *          <p>For more information about key policies, see the <a href="https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html">Amazon Web Services KMS Developer Guide</a>. If
     *             you do not specify an Amazon Web Services KMS key, Amazon SES does not encrypt your emails.</p>
     *          <important>
     *             <p>Your mail is encrypted by Amazon SES using the Amazon S3 encryption client before the mail
     *                 is submitted to Amazon S3 for storage. It is not encrypted using Amazon S3 server-side
     *                 encryption. This means that you must use the Amazon S3 encryption client to decrypt the
     *                 email after retrieving it from Amazon S3, as the service has no access to use your
     *                 Amazon Web Services KMS keys for decryption. This encryption client is currently available with
     *                 the <a href="http://aws.amazon.com/sdk-for-java/">Amazon Web Services SDK for Java</a> and
     *                     <a href="http://aws.amazon.com/sdk-for-ruby/">Amazon Web Services SDK for Ruby</a> only. For
     *                 more information about client-side encryption using Amazon Web Services KMS managed keys, see the
     *                     <a href="https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingClientSideEncryption.html">Amazon S3 Developer Guide</a>.</p>
     *          </important>
     * @public
     */
    KmsKeyArn?: string | undefined;
    /**
     * <p> The ARN of the IAM role to be used by Amazon Simple Email Service while writing to the Amazon S3 bucket,
     *             optionally encrypting your mail via the provided customer managed key, and publishing to
     *             the Amazon SNS topic. This role should have access to the following APIs: </p>
     *          <ul>
     *             <li>
     *                <p>
     *                   <code>s3:PutObject</code>, <code>kms:Encrypt</code> and
     *                         <code>kms:GenerateDataKey</code> for the given Amazon S3 bucket.</p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>kms:GenerateDataKey</code> for the given Amazon Web Services KMS customer managed key.
     *                 </p>
     *             </li>
     *             <li>
     *                <p>
     *                   <code>sns:Publish</code> for the given Amazon SNS topic.</p>
     *             </li>
     *          </ul>
     *          <note>
     *             <p>If an IAM role ARN is provided, the role (and only the role) is used to access all
     *                 the given resources (Amazon S3 bucket, Amazon Web Services KMS customer managed key and Amazon SNS topic).
     *                 Therefore, setting up individual resource access permissions is not required.</p>
     *          </note>
     * @public
     */
    IamRoleArn?: string | undefined;
}
/**
 * @public
 * @enum
 */
export declare const SNSActionEncoding: {
    readonly Base64: "Base64";
    readonly UTF8: "UTF-8";
};
/**
 * @public
 */
export type SNSActionEncoding = (typeof SNSActionEncoding)[keyof typeof SNSActionEncoding];
/**
 * <p>When included in a receipt rule, this action publishes a notification to Amazon Simple Notification Service
 *             (Amazon SNS). This action includes a complete copy of the email content in the Amazon SNS
 *             notifications. Amazon SNS notifications for all other actions simply provide information
 *             about the email. They do not include the email content itself.</p>
 *          <p>If you own the Amazon SNS topic, you don't need to do anything to give Amazon SES permission to
 *             publish emails to it. However, if you don't own the Amazon SNS topic, you need to attach a
 *             policy to the topic to give Amazon SES permissions to access it. For information about giving
 *             permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-permissions.html">Amazon SES Developer
 *             Guide</a>.</p>
 *          <important>
 *             <p>You can only publish emails that are 150 KB or less (including the header) to
 *                 Amazon SNS. Larger emails bounce. If you anticipate emails larger than 150 KB, use the S3
 *                 action instead.</p>
 *          </important>
 *          <p>For information about using a receipt rule to publish an Amazon SNS notification, see the
 *                 <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-sns.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface SNSAction {
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic to notify. You can find the ARN of a
     *             topic by using the <a href="https://docs.aws.amazon.com/sns/latest/api/API_ListTopics.html">ListTopics</a> operation in Amazon SNS.</p>
     *          <p>For more information about Amazon SNS topics, see the <a href="https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html">Amazon SNS Developer Guide</a>.</p>
     * @public
     */
    TopicArn: string | undefined;
    /**
     * <p>The encoding to use for the email within the Amazon SNS notification. UTF-8 is easier to
     *             use, but may not preserve all special characters when a message was encoded with a
     *             different encoding format. Base64 preserves all special characters. The default value is
     *             UTF-8.</p>
     * @public
     */
    Encoding?: SNSActionEncoding | undefined;
}
/**
 * @public
 * @enum
 */
export declare const StopScope: {
    readonly RULE_SET: "RuleSet";
};
/**
 * @public
 */
export type StopScope = (typeof StopScope)[keyof typeof StopScope];
/**
 * <p>When included in a receipt rule, this action terminates the evaluation of the receipt
 *             rule set and, optionally, publishes a notification to Amazon Simple Notification Service (Amazon SNS).</p>
 *          <p>For information about setting a stop action in a receipt rule, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-stop.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface StopAction {
    /**
     * <p>The scope of the StopAction. The only acceptable value is <code>RuleSet</code>.</p>
     * @public
     */
    Scope: StopScope | undefined;
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic to notify when the stop action is
     *             taken. You can find the ARN of a topic by using the <a href="https://docs.aws.amazon.com/sns/latest/api/API_ListTopics.html">ListTopics</a> Amazon SNS operation.</p>
     *          <p>For more information about Amazon SNS topics, see the <a href="https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html">Amazon SNS Developer Guide</a>.</p>
     * @public
     */
    TopicArn?: string | undefined;
}
/**
 * <p>When included in a receipt rule, this action calls Amazon WorkMail and, optionally,
 *             publishes a notification to Amazon Simple Notification Service (Amazon SNS). It usually isn't necessary to set this up
 *             manually, because Amazon WorkMail adds the rule automatically during its setup
 *             procedure.</p>
 *          <p>For information using a receipt rule to call Amazon WorkMail, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-action-workmail.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface WorkmailAction {
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic to notify when the WorkMail action
     *             is called. You can find the ARN of a topic by using the <a href="https://docs.aws.amazon.com/sns/latest/api/API_ListTopics.html">ListTopics</a> operation in
     *             Amazon SNS.</p>
     *          <p>For more information about Amazon SNS topics, see the <a href="https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html">Amazon SNS Developer Guide</a>.</p>
     * @public
     */
    TopicArn?: string | undefined;
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon WorkMail organization. Amazon WorkMail
     *             ARNs use the following format:</p>
     *          <p>
     *             <code>arn:aws:workmail:<region>:<awsAccountId>:organization/<workmailOrganizationId></code>
     *          </p>
     *          <p>You can find the ID of your organization by using the <a href="https://docs.aws.amazon.com/workmail/latest/APIReference/API_ListOrganizations.html">ListOrganizations</a> operation in Amazon WorkMail. Amazon WorkMail
     *             organization IDs begin with "<code>m-</code>", followed by a string of alphanumeric
     *             characters.</p>
     *          <p>For information about Amazon WorkMail organizations, see the <a href="https://docs.aws.amazon.com/workmail/latest/adminguide/organizations_overview.html">Amazon WorkMail Administrator Guide</a>.</p>
     * @public
     */
    OrganizationArn: string | undefined;
}
/**
 * <p>An action that Amazon SES can take when it receives an email on behalf of one or more email
 *             addresses or domains that you own. An instance of this data type can represent only one
 *             action.</p>
 *          <p>For information about setting up receipt rules, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface ReceiptAction {
    /**
     * <p>Saves the received message to an Amazon Simple Storage Service (Amazon S3) bucket and, optionally, publishes a
     *             notification to Amazon SNS.</p>
     * @public
     */
    S3Action?: S3Action | undefined;
    /**
     * <p>Rejects the received email by returning a bounce response to the sender and,
     *             optionally, publishes a notification to Amazon Simple Notification Service (Amazon SNS).</p>
     * @public
     */
    BounceAction?: BounceAction | undefined;
    /**
     * <p>Calls Amazon WorkMail and, optionally, publishes a notification to Amazon
     *             Amazon SNS.</p>
     * @public
     */
    WorkmailAction?: WorkmailAction | undefined;
    /**
     * <p>Calls an Amazon Web Services Lambda function, and optionally, publishes a notification to Amazon SNS.</p>
     * @public
     */
    LambdaAction?: LambdaAction | undefined;
    /**
     * <p>Terminates the evaluation of the receipt rule set and optionally publishes a
     *             notification to Amazon SNS.</p>
     * @public
     */
    StopAction?: StopAction | undefined;
    /**
     * <p>Adds a header to the received email.</p>
     * @public
     */
    AddHeaderAction?: AddHeaderAction | undefined;
    /**
     * <p>Publishes the email content within a notification to Amazon SNS.</p>
     * @public
     */
    SNSAction?: SNSAction | undefined;
    /**
     * <p>Parses the received message and starts an email contact in Amazon Connect on your behalf.</p>
     * @public
     */
    ConnectAction?: ConnectAction | undefined;
}
/**
 * @public
 * @enum
 */
export declare const TlsPolicy: {
    readonly Optional: "Optional";
    readonly Require: "Require";
};
/**
 * @public
 */
export type TlsPolicy = (typeof TlsPolicy)[keyof typeof TlsPolicy];
/**
 * <p>Receipt rules enable you to specify which actions Amazon SES should take when it receives
 *             mail on behalf of one or more email addresses or domains that you own.</p>
 *          <p>Each receipt rule defines a set of email addresses or domains that it applies to. If
 *             the email addresses or domains match at least one recipient address of the message,
 *             Amazon SES executes all of the receipt rule's actions on the message.</p>
 *          <p>For information about setting up receipt rules, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface ReceiptRule {
    /**
     * <p>The name of the receipt rule. The name must meet the following requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), dashes
     *                     (-), or periods (.). </p>
     *             </li>
     *             <li>
     *                <p>Start and end with a letter or number.</p>
     *             </li>
     *             <li>
     *                <p>Contain 64 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Name: string | undefined;
    /**
     * <p>If <code>true</code>, the receipt rule is active. The default value is
     *                 <code>false</code>.</p>
     * @public
     */
    Enabled?: boolean | undefined;
    /**
     * <p>Specifies whether Amazon SES should require that incoming email is delivered over a
     *             connection encrypted with Transport Layer Security (TLS). If this parameter is set to
     *                 <code>Require</code>, Amazon SES bounces emails that are not received over TLS. The
     *             default is <code>Optional</code>.</p>
     * @public
     */
    TlsPolicy?: TlsPolicy | undefined;
    /**
     * <p>The recipient domains and email addresses that the receipt rule applies to. If this
     *             field is not specified, this rule matches all recipients on all verified domains.</p>
     * @public
     */
    Recipients?: string[] | undefined;
    /**
     * <p>An ordered list of actions to perform on messages that match at least one of the
     *             recipient email addresses or domains specified in the receipt rule.</p>
     * @public
     */
    Actions?: ReceiptAction[] | undefined;
    /**
     * <p>If <code>true</code>, then messages that this receipt rule applies to are scanned for
     *             spam and viruses. The default value is <code>false</code>.</p>
     * @public
     */
    ScanEnabled?: boolean | undefined;
}
/**
 * <p>Represents a request to create a receipt rule. You use receipt rules to receive email
 *             with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface CreateReceiptRuleRequest {
    /**
     * <p>The name of the rule set where the receipt rule is added.</p>
     * @public
     */
    RuleSetName: string | undefined;
    /**
     * <p>The name of an existing rule after which the new rule is placed. If this parameter is
     *             null, the new rule is inserted at the beginning of the rule list.</p>
     * @public
     */
    After?: string | undefined;
    /**
     * <p>A data structure that contains the specified rule's name, actions, recipients,
     *             domains, enabled status, scan status, and TLS policy.</p>
     * @public
     */
    Rule: ReceiptRule | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface CreateReceiptRuleResponse {
}
/**
 * <p>Indicates that the provided Amazon Web Services Lambda function is invalid, or that Amazon SES could
 *             not execute the provided function, possibly due to permissions issues. For information
 *             about giving permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-permissions.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export declare class InvalidLambdaFunctionException extends __BaseException {
    readonly name: "InvalidLambdaFunctionException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the ARN of the function was not found.</p>
     * @public
     */
    FunctionArn?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidLambdaFunctionException, __BaseException>);
}
/**
 * <p>Indicates that the provided Amazon S3 bucket or Amazon Web Services KMS encryption key is invalid,
 *             or that Amazon SES could not publish to the bucket, possibly due to permissions issues.
 *             For information about giving permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-permissions.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export declare class InvalidS3ConfigurationException extends __BaseException {
    readonly name: "InvalidS3ConfigurationException";
    readonly $fault: "client";
    /**
     * <p>Indicated that the S3 Bucket was not found.</p>
     * @public
     */
    Bucket?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidS3ConfigurationException, __BaseException>);
}
/**
 * <p>Indicates that the provided Amazon SNS topic is invalid, or that Amazon SES could not
 *             publish to the topic, possibly due to permissions issues. For information about giving
 *             permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-permissions.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export declare class InvalidSnsTopicException extends __BaseException {
    readonly name: "InvalidSnsTopicException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the topic does not exist.</p>
     * @public
     */
    Topic?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidSnsTopicException, __BaseException>);
}
/**
 * <p>Indicates that the provided receipt rule does not exist.</p>
 * @public
 */
export declare class RuleDoesNotExistException extends __BaseException {
    readonly name: "RuleDoesNotExistException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the named receipt rule does not exist.</p>
     * @public
     */
    Name?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<RuleDoesNotExistException, __BaseException>);
}
/**
 * <p>Represents a request to create an empty receipt rule set. You use receipt rule sets to
 *             receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface CreateReceiptRuleSetRequest {
    /**
     * <p>The name of the rule set to create. The name must meet the following
     *             requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), or
     *                     dashes (-).</p>
     *             </li>
     *             <li>
     *                <p>Start and end with a letter or number.</p>
     *             </li>
     *             <li>
     *                <p>Contain 64 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    RuleSetName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface CreateReceiptRuleSetResponse {
}
/**
 * <p>The content of the email, composed of a subject line and either an HTML part or a
 *             text-only part.</p>
 * @public
 */
export interface Template {
    /**
     * <p>The name of the template. You use this name when you send email using the
     *                 <code>SendTemplatedEmail</code> or <code>SendBulkTemplatedEmail</code>
     *             operations.</p>
     * @public
     */
    TemplateName: string | undefined;
    /**
     * <p>The subject line of the email.</p>
     * @public
     */
    SubjectPart?: string | undefined;
    /**
     * <p>The email body that is visible to recipients whose email clients do not display HTML
     *             content.</p>
     * @public
     */
    TextPart?: string | undefined;
    /**
     * <p>The HTML body of the email.</p>
     * @public
     */
    HtmlPart?: string | undefined;
}
/**
 * <p>Represents a request to create an email template. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-personalized-email-api.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface CreateTemplateRequest {
    /**
     * <p>The content of the email, composed of a subject line and either an HTML part or a
     *             text-only part.</p>
     * @public
     */
    Template: Template | undefined;
}
/**
 * @public
 */
export interface CreateTemplateResponse {
}
/**
 * <p>Indicates that the template that you specified could not be rendered. This issue may
 *             occur when a template refers to a partial that does not exist.</p>
 * @public
 */
export declare class InvalidTemplateException extends __BaseException {
    readonly name: "InvalidTemplateException";
    readonly $fault: "client";
    TemplateName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidTemplateException, __BaseException>);
}
/**
 * @public
 * @enum
 */
export declare const CustomMailFromStatus: {
    readonly Failed: "Failed";
    readonly Pending: "Pending";
    readonly Success: "Success";
    readonly TemporaryFailure: "TemporaryFailure";
};
/**
 * @public
 */
export type CustomMailFromStatus = (typeof CustomMailFromStatus)[keyof typeof CustomMailFromStatus];
/**
 * <p>Contains information about a custom verification email template.</p>
 * @public
 */
export interface CustomVerificationEmailTemplate {
    /**
     * <p>The name of the custom verification email template.</p>
     * @public
     */
    TemplateName?: string | undefined;
    /**
     * <p>The email address that the custom verification email is sent from.</p>
     * @public
     */
    FromEmailAddress?: string | undefined;
    /**
     * <p>The subject line of the custom verification email.</p>
     * @public
     */
    TemplateSubject?: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is successfully verified.</p>
     * @public
     */
    SuccessRedirectionURL?: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is not successfully verified.</p>
     * @public
     */
    FailureRedirectionURL?: string | undefined;
}
/**
 * <p>Indicates that a custom verification email template with the name you specified does
 *             not exist.</p>
 * @public
 */
export declare class CustomVerificationEmailTemplateDoesNotExistException extends __BaseException {
    readonly name: "CustomVerificationEmailTemplateDoesNotExistException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the provided custom verification email template does not exist.</p>
     * @public
     */
    CustomVerificationEmailTemplateName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<CustomVerificationEmailTemplateDoesNotExistException, __BaseException>);
}
/**
 * <p>Represents a request to delete a configuration set. Configuration sets enable you to
 *             publish email sending events. For information about using configuration sets, see the
 *                 <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface DeleteConfigurationSetRequest {
    /**
     * <p>The name of the configuration set to delete.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteConfigurationSetResponse {
}
/**
 * <p>Represents a request to delete a configuration set event destination. Configuration
 *             set event destinations are associated with configuration sets, which enable you to
 *             publish email sending events. For information about using configuration sets, see the
 *                 <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface DeleteConfigurationSetEventDestinationRequest {
    /**
     * <p>The name of the configuration set from which to delete the event destination.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>The name of the event destination to delete.</p>
     * @public
     */
    EventDestinationName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteConfigurationSetEventDestinationResponse {
}
/**
 * <p>Indicates that the event destination does not exist.</p>
 * @public
 */
export declare class EventDestinationDoesNotExistException extends __BaseException {
    readonly name: "EventDestinationDoesNotExistException";
    readonly $fault: "client";
    /**
     * <p>Indicates that the configuration set does not exist.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * <p>Indicates that the event destination does not exist.</p>
     * @public
     */
    EventDestinationName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<EventDestinationDoesNotExistException, __BaseException>);
}
/**
 * <p>Represents a request to delete open and click tracking options in a configuration set.
 *         </p>
 * @public
 */
export interface DeleteConfigurationSetTrackingOptionsRequest {
    /**
     * <p>The name of the configuration set.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteConfigurationSetTrackingOptionsResponse {
}
/**
 * <p>Indicates that the TrackingOptions object you specified does not exist.</p>
 * @public
 */
export declare class TrackingOptionsDoesNotExistException extends __BaseException {
    readonly name: "TrackingOptionsDoesNotExistException";
    readonly $fault: "client";
    /**
     * <p>Indicates that a TrackingOptions object does not exist in the specified configuration
     *             set.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<TrackingOptionsDoesNotExistException, __BaseException>);
}
/**
 * <p>Represents a request to delete an existing custom verification email template.</p>
 * @public
 */
export interface DeleteCustomVerificationEmailTemplateRequest {
    /**
     * <p>The name of the custom verification email template to delete.</p>
     * @public
     */
    TemplateName: string | undefined;
}
/**
 * <p>Represents a request to delete one of your Amazon SES identities (an email address or
 *             domain).</p>
 * @public
 */
export interface DeleteIdentityRequest {
    /**
     * <p>The identity to be removed from the list of identities for the Amazon Web Services account.</p>
     * @public
     */
    Identity: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteIdentityResponse {
}
/**
 * <p>Represents a request to delete a sending authorization policy for an identity. Sending
 *             authorization is an Amazon SES feature that enables you to authorize other senders to use
 *             your identities. For information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface DeleteIdentityPolicyRequest {
    /**
     * <p>The identity that is associated with the policy to delete. You can specify the
     *             identity by using its name or by using its Amazon Resource Name (ARN). Examples:
     *                 <code>user@example.com</code>, <code>example.com</code>,
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>.</p>
     *          <p>To successfully call this operation, you must own the identity.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>The name of the policy to be deleted.</p>
     * @public
     */
    PolicyName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteIdentityPolicyResponse {
}
/**
 * <p>Represents a request to delete an IP address filter. You use IP address filters when
 *             you receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface DeleteReceiptFilterRequest {
    /**
     * <p>The name of the IP address filter to delete.</p>
     * @public
     */
    FilterName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteReceiptFilterResponse {
}
/**
 * <p>Represents a request to delete a receipt rule. You use receipt rules to receive email
 *             with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface DeleteReceiptRuleRequest {
    /**
     * <p>The name of the receipt rule set that contains the receipt rule to delete.</p>
     * @public
     */
    RuleSetName: string | undefined;
    /**
     * <p>The name of the receipt rule to delete.</p>
     * @public
     */
    RuleName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteReceiptRuleResponse {
}
/**
 * <p>Represents a request to delete a receipt rule set and all of the receipt rules it
 *             contains. You use receipt rule sets to receive email with Amazon SES. For more information,
 *             see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface DeleteReceiptRuleSetRequest {
    /**
     * <p>The name of the receipt rule set to delete.</p>
     * @public
     */
    RuleSetName: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface DeleteReceiptRuleSetResponse {
}
/**
 * <p>Represents a request to delete an email template. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-personalized-email-api.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface DeleteTemplateRequest {
    /**
     * <p>The name of the template to be deleted.</p>
     * @public
     */
    TemplateName: string | undefined;
}
/**
 * @public
 */
export interface DeleteTemplateResponse {
}
/**
 * <p>Represents a request to delete an email address from the list of email addresses you
 *             have attempted to verify under your Amazon Web Services account.</p>
 * @public
 */
export interface DeleteVerifiedEmailAddressRequest {
    /**
     * <p>An email address to be removed from the list of verified addresses.</p>
     * @public
     */
    EmailAddress: string | undefined;
}
/**
 * <p>Specifies whether messages that use the configuration set are required to use
 *             Transport Layer Security (TLS).</p>
 * @public
 */
export interface DeliveryOptions {
    /**
     * <p>Specifies whether messages that use the configuration set are required to use
     *             Transport Layer Security (TLS). If the value is <code>Require</code>, messages are only
     *             delivered if a TLS connection can be established. If the value is <code>Optional</code>,
     *             messages can be delivered in plain text if a TLS connection can't be established.</p>
     * @public
     */
    TlsPolicy?: TlsPolicy | undefined;
}
/**
 * <p>Represents a request to return the metadata and receipt rules for the receipt rule set
 *             that is currently active. You use receipt rule sets to receive email with Amazon SES. For
 *             more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface DescribeActiveReceiptRuleSetRequest {
}
/**
 * <p>Information about a receipt rule set.</p>
 *          <p>A receipt rule set is a collection of rules that specify what Amazon SES should do with
 *             mail it receives on behalf of your account's verified domains.</p>
 *          <p>For information about setting up receipt rule sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html#receiving-email-concepts-rules">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface ReceiptRuleSetMetadata {
    /**
     * <p>The name of the receipt rule set. The name must meet the following
     *             requirements:</p>
     *          <ul>
     *             <li>
     *                <p>Contain only ASCII letters (a-z, A-Z), numbers (0-9), underscores (_), or
     *                     dashes (-).</p>
     *             </li>
     *             <li>
     *                <p>Start and end with a letter or number.</p>
     *             </li>
     *             <li>
     *                <p>Contain 64 characters or fewer.</p>
     *             </li>
     *          </ul>
     * @public
     */
    Name?: string | undefined;
    /**
     * <p>The date and time the receipt rule set was created.</p>
     * @public
     */
    CreatedTimestamp?: Date | undefined;
}
/**
 * <p>Represents the metadata and receipt rules for the receipt rule set that is currently
 *             active.</p>
 * @public
 */
export interface DescribeActiveReceiptRuleSetResponse {
    /**
     * <p>The metadata for the currently active receipt rule set. The metadata consists of the
     *             rule set name and a timestamp of when the rule set was created.</p>
     * @public
     */
    Metadata?: ReceiptRuleSetMetadata | undefined;
    /**
     * <p>The receipt rules that belong to the active rule set.</p>
     * @public
     */
    Rules?: ReceiptRule[] | undefined;
}
/**
 * <p>Represents a request to return the details of a configuration set. Configuration sets
 *             enable you to publish email sending events. For information about using configuration
 *             sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface DescribeConfigurationSetRequest {
    /**
     * <p>The name of the configuration set to describe.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>A list of configuration set attributes to return.</p>
     * @public
     */
    ConfigurationSetAttributeNames?: ConfigurationSetAttribute[] | undefined;
}
/**
 * <p>Contains information about the reputation settings for a configuration set.</p>
 * @public
 */
export interface ReputationOptions {
    /**
     * <p>Describes whether email sending is enabled or disabled for the configuration set. If
     *             the value is <code>true</code>, then Amazon SES sends emails that use the configuration set.
     *             If the value is <code>false</code>, Amazon SES does not send emails that use the
     *             configuration set. The default value is <code>true</code>. You can change this setting
     *             using <a>UpdateConfigurationSetSendingEnabled</a>.</p>
     * @public
     */
    SendingEnabled?: boolean | undefined;
    /**
     * <p>Describes whether or not Amazon SES publishes reputation metrics for the configuration set,
     *             such as bounce and complaint rates, to Amazon CloudWatch.</p>
     *          <p>If the value is <code>true</code>, reputation metrics are published. If the value is
     *                 <code>false</code>, reputation metrics are not published. The default value is
     *                 <code>false</code>.</p>
     * @public
     */
    ReputationMetricsEnabled?: boolean | undefined;
    /**
     * <p>The date and time at which the reputation metrics for the configuration set were last
     *             reset. Resetting these metrics is known as a <i>fresh start</i>.</p>
     *          <p>When you disable email sending for a configuration set using <a>UpdateConfigurationSetSendingEnabled</a> and later re-enable it, the
     *             reputation metrics for the configuration set (but not for the entire Amazon SES account) are
     *             reset.</p>
     *          <p>If email sending for the configuration set has never been disabled and later
     *             re-enabled, the value of this attribute is <code>null</code>.</p>
     * @public
     */
    LastFreshStart?: Date | undefined;
}
/**
 * <p>Represents the details of a configuration set. Configuration sets enable you to
 *             publish email sending events. For information about using configuration sets, see the
 *                 <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface DescribeConfigurationSetResponse {
    /**
     * <p>The configuration set object associated with the specified configuration set.</p>
     * @public
     */
    ConfigurationSet?: ConfigurationSet | undefined;
    /**
     * <p>A list of event destinations associated with the configuration set. </p>
     * @public
     */
    EventDestinations?: EventDestination[] | undefined;
    /**
     * <p>The name of the custom open and click tracking domain associated with the
     *             configuration set.</p>
     * @public
     */
    TrackingOptions?: TrackingOptions | undefined;
    /**
     * <p>Specifies whether messages that use the configuration set are required to use
     *             Transport Layer Security (TLS).</p>
     * @public
     */
    DeliveryOptions?: DeliveryOptions | undefined;
    /**
     * <p>An object that represents the reputation settings for the configuration set. </p>
     * @public
     */
    ReputationOptions?: ReputationOptions | undefined;
}
/**
 * <p>Represents a request to return the details of a receipt rule. You use receipt rules to
 *             receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface DescribeReceiptRuleRequest {
    /**
     * <p>The name of the receipt rule set that the receipt rule belongs to.</p>
     * @public
     */
    RuleSetName: string | undefined;
    /**
     * <p>The name of the receipt rule.</p>
     * @public
     */
    RuleName: string | undefined;
}
/**
 * <p>Represents the details of a receipt rule.</p>
 * @public
 */
export interface DescribeReceiptRuleResponse {
    /**
     * <p>A data structure that contains the specified receipt rule's name, actions, recipients,
     *             domains, enabled status, scan status, and Transport Layer Security (TLS) policy.</p>
     * @public
     */
    Rule?: ReceiptRule | undefined;
}
/**
 * <p>Represents a request to return the details of a receipt rule set. You use receipt rule
 *             sets to receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface DescribeReceiptRuleSetRequest {
    /**
     * <p>The name of the receipt rule set to describe.</p>
     * @public
     */
    RuleSetName: string | undefined;
}
/**
 * <p>Represents the details of the specified receipt rule set.</p>
 * @public
 */
export interface DescribeReceiptRuleSetResponse {
    /**
     * <p>The metadata for the receipt rule set, which consists of the rule set name and the
     *             timestamp of when the rule set was created.</p>
     * @public
     */
    Metadata?: ReceiptRuleSetMetadata | undefined;
    /**
     * <p>A list of the receipt rules that belong to the specified receipt rule set.</p>
     * @public
     */
    Rules?: ReceiptRule[] | undefined;
}
/**
 * @public
 * @enum
 */
export declare const VerificationStatus: {
    readonly Failed: "Failed";
    readonly NotStarted: "NotStarted";
    readonly Pending: "Pending";
    readonly Success: "Success";
    readonly TemporaryFailure: "TemporaryFailure";
};
/**
 * @public
 */
export type VerificationStatus = (typeof VerificationStatus)[keyof typeof VerificationStatus];
/**
 * <p>Represents the DKIM attributes of a verified email address or a domain.</p>
 * @public
 */
export interface IdentityDkimAttributes {
    /**
     * <p>Is true if DKIM signing is enabled for email sent from the identity. It's false
     *             otherwise. The default value is true.</p>
     * @public
     */
    DkimEnabled: boolean | undefined;
    /**
     * <p>Describes whether Amazon SES has successfully verified the DKIM DNS records (tokens)
     *             published in the domain name's DNS. (This only applies to domain identities, not email
     *             address identities.)</p>
     * @public
     */
    DkimVerificationStatus: VerificationStatus | undefined;
    /**
     * <p>A set of character strings that represent the domain's identity. Using these tokens,
     *             you need to create DNS CNAME records that point to DKIM public keys that are hosted by
     *             Amazon SES. Amazon Web Services eventually detects that you've updated your DNS records. This detection
     *             process might take up to 72 hours. After successful detection, Amazon SES is able to
     *             DKIM-sign email originating from that domain. (This only applies to domain identities,
     *             not email address identities.)</p>
     *          <p>For more information about creating DNS records using DKIM tokens, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    DkimTokens?: string[] | undefined;
}
/**
 * <p>Represents a request to return the email sending status for your Amazon SES account in the
 *             current Amazon Web Services Region.</p>
 * @public
 */
export interface GetAccountSendingEnabledResponse {
    /**
     * <p>Describes whether email sending is enabled or disabled for your Amazon SES account in the
     *             current Amazon Web Services Region.</p>
     * @public
     */
    Enabled?: boolean | undefined;
}
/**
 * <p>Represents a request to retrieve an existing custom verification email
 *             template.</p>
 * @public
 */
export interface GetCustomVerificationEmailTemplateRequest {
    /**
     * <p>The name of the custom verification email template to retrieve.</p>
     * @public
     */
    TemplateName: string | undefined;
}
/**
 * <p>The content of the custom verification email template.</p>
 * @public
 */
export interface GetCustomVerificationEmailTemplateResponse {
    /**
     * <p>The name of the custom verification email template.</p>
     * @public
     */
    TemplateName?: string | undefined;
    /**
     * <p>The email address that the custom verification email is sent from.</p>
     * @public
     */
    FromEmailAddress?: string | undefined;
    /**
     * <p>The subject line of the custom verification email.</p>
     * @public
     */
    TemplateSubject?: string | undefined;
    /**
     * <p>The content of the custom verification email.</p>
     * @public
     */
    TemplateContent?: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is successfully verified.</p>
     * @public
     */
    SuccessRedirectionURL?: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is not successfully verified.</p>
     * @public
     */
    FailureRedirectionURL?: string | undefined;
}
/**
 * <p>Represents a request for the status of Amazon SES Easy DKIM signing for an identity. For
 *             domain identities, this request also returns the DKIM tokens that are required for Easy
 *             DKIM signing, and whether Amazon SES successfully verified that these tokens were published.
 *             For more information about Easy DKIM, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface GetIdentityDkimAttributesRequest {
    /**
     * <p>A list of one or more verified identities - email addresses, domains, or both.</p>
     * @public
     */
    Identities: string[] | undefined;
}
/**
 * <p>Represents the status of Amazon SES Easy DKIM signing for an identity. For domain
 *             identities, this response also contains the DKIM tokens that are required for Easy DKIM
 *             signing, and whether Amazon SES successfully verified that these tokens were
 *             published.</p>
 * @public
 */
export interface GetIdentityDkimAttributesResponse {
    /**
     * <p>The DKIM attributes for an email address or a domain.</p>
     * @public
     */
    DkimAttributes: Record<string, IdentityDkimAttributes> | undefined;
}
/**
 * <p>Represents a request to return the Amazon SES custom MAIL FROM attributes for a list of
 *             identities. For information about using a custom MAIL FROM domain, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/mail-from.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface GetIdentityMailFromDomainAttributesRequest {
    /**
     * <p>A list of one or more identities.</p>
     * @public
     */
    Identities: string[] | undefined;
}
/**
 * <p>Represents the custom MAIL FROM domain attributes of a verified identity (email
 *             address or domain).</p>
 * @public
 */
export interface IdentityMailFromDomainAttributes {
    /**
     * <p>The custom MAIL FROM domain that the identity is configured to use.</p>
     * @public
     */
    MailFromDomain: string | undefined;
    /**
     * <p>The state that indicates whether Amazon SES has successfully read the MX record required
     *             for custom MAIL FROM domain setup. If the state is <code>Success</code>, Amazon SES uses the
     *             specified custom MAIL FROM domain when the verified identity sends an email. All other
     *             states indicate that Amazon SES takes the action described by
     *                 <code>BehaviorOnMXFailure</code>.</p>
     * @public
     */
    MailFromDomainStatus: CustomMailFromStatus | undefined;
    /**
     * <p>The action that Amazon SES takes if it cannot successfully read the required MX record when
     *             you send an email. A value of <code>UseDefaultValue</code> indicates that if Amazon SES
     *             cannot read the required MX record, it uses amazonses.com (or a subdomain of that) as
     *             the MAIL FROM domain. A value of <code>RejectMessage</code> indicates that if Amazon SES
     *             cannot read the required MX record, Amazon SES returns a
     *                 <code>MailFromDomainNotVerified</code> error and does not send the email.</p>
     *          <p>The custom MAIL FROM setup states that result in this behavior are
     *                 <code>Pending</code>, <code>Failed</code>, and <code>TemporaryFailure</code>.</p>
     * @public
     */
    BehaviorOnMXFailure: BehaviorOnMXFailure | undefined;
}
/**
 * <p>Represents the custom MAIL FROM attributes for a list of identities.</p>
 * @public
 */
export interface GetIdentityMailFromDomainAttributesResponse {
    /**
     * <p>A map of identities to custom MAIL FROM attributes.</p>
     * @public
     */
    MailFromDomainAttributes: Record<string, IdentityMailFromDomainAttributes> | undefined;
}
/**
 * <p>Represents a request to return the notification attributes for a list of identities
 *             you verified with Amazon SES. For information about Amazon SES notifications, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface GetIdentityNotificationAttributesRequest {
    /**
     * <p>A list of one or more identities. You can specify an identity by using its name or by
     *             using its Amazon Resource Name (ARN). Examples: <code>user@example.com</code>,
     *                 <code>example.com</code>,
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>.</p>
     * @public
     */
    Identities: string[] | undefined;
}
/**
 * <p>Represents the notification attributes of an identity, including whether an identity
 *             has Amazon Simple Notification Service (Amazon SNS) topics set for bounce, complaint, and/or delivery notifications,
 *             and whether feedback forwarding is enabled for bounce and complaint
 *             notifications.</p>
 * @public
 */
export interface IdentityNotificationAttributes {
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic where Amazon SES publishes bounce
     *             notifications.</p>
     * @public
     */
    BounceTopic: string | undefined;
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic where Amazon SES publishes complaint
     *             notifications.</p>
     * @public
     */
    ComplaintTopic: string | undefined;
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic where Amazon SES publishes delivery
     *             notifications.</p>
     * @public
     */
    DeliveryTopic: string | undefined;
    /**
     * <p>Describes whether Amazon SES forwards bounce and complaint notifications as email.
     *                 <code>true</code> indicates that Amazon SES forwards bounce and complaint notifications
     *             as email, while <code>false</code> indicates that bounce and complaint notifications are
     *             published only to the specified bounce and complaint Amazon SNS topics.</p>
     * @public
     */
    ForwardingEnabled: boolean | undefined;
    /**
     * <p>Describes whether Amazon SES includes the original email headers in Amazon SNS notifications of
     *             type <code>Bounce</code>. A value of <code>true</code> specifies that Amazon SES includes
     *             headers in bounce notifications, and a value of <code>false</code> specifies that Amazon SES
     *             does not include headers in bounce notifications.</p>
     * @public
     */
    HeadersInBounceNotificationsEnabled?: boolean | undefined;
    /**
     * <p>Describes whether Amazon SES includes the original email headers in Amazon SNS notifications of
     *             type <code>Complaint</code>. A value of <code>true</code> specifies that Amazon SES includes
     *             headers in complaint notifications, and a value of <code>false</code> specifies that
     *             Amazon SES does not include headers in complaint notifications.</p>
     * @public
     */
    HeadersInComplaintNotificationsEnabled?: boolean | undefined;
    /**
     * <p>Describes whether Amazon SES includes the original email headers in Amazon SNS notifications of
     *             type <code>Delivery</code>. A value of <code>true</code> specifies that Amazon SES includes
     *             headers in delivery notifications, and a value of <code>false</code> specifies that
     *             Amazon SES does not include headers in delivery notifications.</p>
     * @public
     */
    HeadersInDeliveryNotificationsEnabled?: boolean | undefined;
}
/**
 * <p>Represents the notification attributes for a list of identities.</p>
 * @public
 */
export interface GetIdentityNotificationAttributesResponse {
    /**
     * <p>A map of Identity to IdentityNotificationAttributes.</p>
     * @public
     */
    NotificationAttributes: Record<string, IdentityNotificationAttributes> | undefined;
}
/**
 * <p>Represents a request to return the requested sending authorization policies for an
 *             identity. Sending authorization is an Amazon SES feature that enables you to authorize other
 *             senders to use your identities. For information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface GetIdentityPoliciesRequest {
    /**
     * <p>The identity for which the policies are retrieved. You can specify an identity by
     *             using its name or by using its Amazon Resource Name (ARN). Examples:
     *                 <code>user@example.com</code>, <code>example.com</code>,
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>.</p>
     *          <p>To successfully call this operation, you must own the identity.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>A list of the names of policies to be retrieved. You can retrieve a maximum of 20
     *             policies at a time. If you do not know the names of the policies that are attached to
     *             the identity, you can use <code>ListIdentityPolicies</code>.</p>
     * @public
     */
    PolicyNames: string[] | undefined;
}
/**
 * <p>Represents the requested sending authorization policies.</p>
 * @public
 */
export interface GetIdentityPoliciesResponse {
    /**
     * <p>A map of policy names to policies.</p>
     * @public
     */
    Policies: Record<string, string> | undefined;
}
/**
 * <p>Represents a request to return the Amazon SES verification status of a list of identities.
 *             For domain identities, this request also returns the verification token. For information
 *             about verifying identities with Amazon SES, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface GetIdentityVerificationAttributesRequest {
    /**
     * <p>A list of identities.</p>
     * @public
     */
    Identities: string[] | undefined;
}
/**
 * <p>Represents the verification attributes of a single identity.</p>
 * @public
 */
export interface IdentityVerificationAttributes {
    /**
     * <p>The verification status of the identity: "Pending", "Success", "Failed", or
     *             "TemporaryFailure".</p>
     * @public
     */
    VerificationStatus: VerificationStatus | undefined;
    /**
     * <p>The verification token for a domain identity. Null for email address
     *             identities.</p>
     * @public
     */
    VerificationToken?: string | undefined;
}
/**
 * <p>The Amazon SES verification status of a list of identities. For domain identities, this
 *             response also contains the verification token.</p>
 * @public
 */
export interface GetIdentityVerificationAttributesResponse {
    /**
     * <p>A map of Identities to IdentityVerificationAttributes objects.</p>
     * @public
     */
    VerificationAttributes: Record<string, IdentityVerificationAttributes> | undefined;
}
/**
 * <p>Represents your Amazon SES daily sending quota, maximum send rate, and the number of emails
 *             you have sent in the last 24 hours.</p>
 * @public
 */
export interface GetSendQuotaResponse {
    /**
     * <p>The maximum number of emails the user is allowed to send in a 24-hour interval. A
     *             value of -1 signifies an unlimited quota.</p>
     * @public
     */
    Max24HourSend?: number | undefined;
    /**
     * <p>The maximum number of emails that Amazon SES can accept from the user's account per
     *             second.</p>
     *          <note>
     *             <p>The rate at which Amazon SES accepts the user's messages might be less than the maximum
     *                 send rate.</p>
     *          </note>
     * @public
     */
    MaxSendRate?: number | undefined;
    /**
     * <p>The number of emails sent during the previous 24 hours.</p>
     * @public
     */
    SentLast24Hours?: number | undefined;
}
/**
 * <p>Represents sending statistics data. Each <code>SendDataPoint</code> contains
 *             statistics for a 15-minute period of sending activity. </p>
 * @public
 */
export interface SendDataPoint {
    /**
     * <p>Time of the data point.</p>
     * @public
     */
    Timestamp?: Date | undefined;
    /**
     * <p>Number of emails that have been sent.</p>
     * @public
     */
    DeliveryAttempts?: number | undefined;
    /**
     * <p>Number of emails that have bounced.</p>
     * @public
     */
    Bounces?: number | undefined;
    /**
     * <p>Number of unwanted emails that were rejected by recipients.</p>
     * @public
     */
    Complaints?: number | undefined;
    /**
     * <p>Number of emails rejected by Amazon SES.</p>
     * @public
     */
    Rejects?: number | undefined;
}
/**
 * <p>Represents a list of data points. This list contains aggregated data from the previous
 *             two weeks of your sending activity with Amazon SES.</p>
 * @public
 */
export interface GetSendStatisticsResponse {
    /**
     * <p>A list of data points, each of which represents 15 minutes of activity.</p>
     * @public
     */
    SendDataPoints?: SendDataPoint[] | undefined;
}
/**
 * @public
 */
export interface GetTemplateRequest {
    /**
     * <p>The name of the template to retrieve.</p>
     * @public
     */
    TemplateName: string | undefined;
}
/**
 * @public
 */
export interface GetTemplateResponse {
    /**
     * <p>The content of the email, composed of a subject line and either an HTML part or a
     *             text-only part.</p>
     * @public
     */
    Template?: Template | undefined;
}
/**
 * <p>Indicates that the Template object you specified does not exist in your Amazon SES
 *             account.</p>
 * @public
 */
export declare class TemplateDoesNotExistException extends __BaseException {
    readonly name: "TemplateDoesNotExistException";
    readonly $fault: "client";
    TemplateName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<TemplateDoesNotExistException, __BaseException>);
}
/**
 * @public
 * @enum
 */
export declare const IdentityType: {
    readonly Domain: "Domain";
    readonly EmailAddress: "EmailAddress";
};
/**
 * @public
 */
export type IdentityType = (typeof IdentityType)[keyof typeof IdentityType];
/**
 * <p>Indicates that provided delivery option is invalid.</p>
 * @public
 */
export declare class InvalidDeliveryOptionsException extends __BaseException {
    readonly name: "InvalidDeliveryOptionsException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidDeliveryOptionsException, __BaseException>);
}
/**
 * <p>Indicates that the provided policy is invalid. Check the error stack for more
 *             information about what caused the error.</p>
 * @public
 */
export declare class InvalidPolicyException extends __BaseException {
    readonly name: "InvalidPolicyException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidPolicyException, __BaseException>);
}
/**
 * <p>Indicates that one or more of the replacement values you provided is invalid. This
 *             error may occur when the TemplateData object contains invalid JSON.</p>
 * @public
 */
export declare class InvalidRenderingParameterException extends __BaseException {
    readonly name: "InvalidRenderingParameterException";
    readonly $fault: "client";
    TemplateName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<InvalidRenderingParameterException, __BaseException>);
}
/**
 * <p>Represents a request to list the configuration sets associated with your
 *             Amazon Web Services account. Configuration sets enable you to publish email sending events. For
 *             information about using configuration sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface ListConfigurationSetsRequest {
    /**
     * <p>A token returned from a previous call to <code>ListConfigurationSets</code> to
     *             indicate the position of the configuration set in the configuration set list.</p>
     * @public
     */
    NextToken?: string | undefined;
    /**
     * <p>The number of configuration sets to return.</p>
     * @public
     */
    MaxItems?: number | undefined;
}
/**
 * <p>A list of configuration sets associated with your Amazon Web Services account. Configuration sets
 *             enable you to publish email sending events. For information about using configuration
 *             sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface ListConfigurationSetsResponse {
    /**
     * <p>A list of configuration sets.</p>
     * @public
     */
    ConfigurationSets?: ConfigurationSet[] | undefined;
    /**
     * <p>A token indicating that there are additional configuration sets available to be
     *             listed. Pass this token to successive calls of <code>ListConfigurationSets</code>.
     *         </p>
     * @public
     */
    NextToken?: string | undefined;
}
/**
 * <p>Represents a request to list the existing custom verification email templates for your
 *             account.</p>
 *          <p>For more information about custom verification email templates, see <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#send-email-verify-address-custom">Using
 *                 Custom Verification Email Templates</a> in the <i>Amazon SES Developer
 *                 Guide</i>.</p>
 * @public
 */
export interface ListCustomVerificationEmailTemplatesRequest {
    /**
     * <p>An array the contains the name and creation time stamp for each template in your Amazon SES
     *             account.</p>
     * @public
     */
    NextToken?: string | undefined;
    /**
     * <p>The maximum number of custom verification email templates to return. This value must
     *             be at least 1 and less than or equal to 50. If you do not specify a value, or if you
     *             specify a value less than 1 or greater than 50, the operation returns up to 50
     *             results.</p>
     * @public
     */
    MaxResults?: number | undefined;
}
/**
 * <p>A paginated list of custom verification email templates.</p>
 * @public
 */
export interface ListCustomVerificationEmailTemplatesResponse {
    /**
     * <p>A list of the custom verification email templates that exist in your account.</p>
     * @public
     */
    CustomVerificationEmailTemplates?: CustomVerificationEmailTemplate[] | undefined;
    /**
     * <p>A token indicating that there are additional custom verification email templates
     *             available to be listed. Pass this token to a subsequent call to
     *                 <code>ListTemplates</code> to retrieve the next 50 custom verification email
     *             templates.</p>
     * @public
     */
    NextToken?: string | undefined;
}
/**
 * <p>Represents a request to return a list of all identities (email addresses and domains)
 *             that you have attempted to verify under your Amazon Web Services account, regardless of verification
 *             status.</p>
 * @public
 */
export interface ListIdentitiesRequest {
    /**
     * <p>The type of the identities to list. Possible values are "EmailAddress" and "Domain".
     *             If this parameter is omitted, then all identities are listed.</p>
     * @public
     */
    IdentityType?: IdentityType | undefined;
    /**
     * <p>The token to use for pagination.</p>
     * @public
     */
    NextToken?: string | undefined;
    /**
     * <p>The maximum number of identities per page. Possible values are 1-1000
     *             inclusive.</p>
     * @public
     */
    MaxItems?: number | undefined;
}
/**
 * <p>A list of all identities that you have attempted to verify under your Amazon Web Services account,
 *             regardless of verification status.</p>
 * @public
 */
export interface ListIdentitiesResponse {
    /**
     * <p>A list of identities.</p>
     * @public
     */
    Identities: string[] | undefined;
    /**
     * <p>The token used for pagination.</p>
     * @public
     */
    NextToken?: string | undefined;
}
/**
 * <p>Represents a request to return a list of sending authorization policies that are
 *             attached to an identity. Sending authorization is an Amazon SES feature that enables you to
 *             authorize other senders to use your identities. For information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface ListIdentityPoliciesRequest {
    /**
     * <p>The identity that is associated with the policy for which the policies are listed. You
     *             can specify an identity by using its name or by using its Amazon Resource Name (ARN).
     *             Examples: <code>user@example.com</code>, <code>example.com</code>,
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>.</p>
     *          <p>To successfully call this operation, you must own the identity.</p>
     * @public
     */
    Identity: string | undefined;
}
/**
 * <p>A list of names of sending authorization policies that apply to an identity.</p>
 * @public
 */
export interface ListIdentityPoliciesResponse {
    /**
     * <p>A list of names of policies that apply to the specified identity.</p>
     * @public
     */
    PolicyNames: string[] | undefined;
}
/**
 * <p>Represents a request to list the IP address filters that exist under your
 *             Amazon Web Services account. You use IP address filters when you receive email with Amazon SES. For more
 *             information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface ListReceiptFiltersRequest {
}
/**
 * <p>A list of IP address filters that exist under your Amazon Web Services account.</p>
 * @public
 */
export interface ListReceiptFiltersResponse {
    /**
     * <p>A list of IP address filter data structures, which each consist of a name, an IP
     *             address range, and whether to allow or block mail from it.</p>
     * @public
     */
    Filters?: ReceiptFilter[] | undefined;
}
/**
 * <p>Represents a request to list the receipt rule sets that exist under your
 *             Amazon Web Services account. You use receipt rule sets to receive email with Amazon SES. For more
 *             information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface ListReceiptRuleSetsRequest {
    /**
     * <p>A token returned from a previous call to <code>ListReceiptRuleSets</code> to indicate
     *             the position in the receipt rule set list.</p>
     * @public
     */
    NextToken?: string | undefined;
}
/**
 * <p>A list of receipt rule sets that exist under your Amazon Web Services account.</p>
 * @public
 */
export interface ListReceiptRuleSetsResponse {
    /**
     * <p>The metadata for the currently active receipt rule set. The metadata consists of the
     *             rule set name and the timestamp of when the rule set was created.</p>
     * @public
     */
    RuleSets?: ReceiptRuleSetMetadata[] | undefined;
    /**
     * <p>A token indicating that there are additional receipt rule sets available to be listed.
     *             Pass this token to successive calls of <code>ListReceiptRuleSets</code> to retrieve up
     *             to 100 receipt rule sets at a time.</p>
     * @public
     */
    NextToken?: string | undefined;
}
/**
 * @public
 */
export interface ListTemplatesRequest {
    /**
     * <p>A token returned from a previous call to <code>ListTemplates</code> to indicate the
     *             position in the list of email templates.</p>
     * @public
     */
    NextToken?: string | undefined;
    /**
     * <p>The maximum number of templates to return. This value must be at least 1 and less than
     *             or equal to 100. If more than 100 items are requested, the page size will automatically
     *             set to 100. If you do not specify a value, 10 is the default page size. </p>
     * @public
     */
    MaxItems?: number | undefined;
}
/**
 * <p>Contains information about an email template.</p>
 * @public
 */
export interface TemplateMetadata {
    /**
     * <p>The name of the template.</p>
     * @public
     */
    Name?: string | undefined;
    /**
     * <p>The time and date the template was created.</p>
     * @public
     */
    CreatedTimestamp?: Date | undefined;
}
/**
 * @public
 */
export interface ListTemplatesResponse {
    /**
     * <p>An array the contains the name and creation time stamp for each template in your Amazon SES
     *             account.</p>
     * @public
     */
    TemplatesMetadata?: TemplateMetadata[] | undefined;
    /**
     * <p>A token indicating that there are additional email templates available to be listed.
     *             Pass this token to a subsequent call to <code>ListTemplates</code> to retrieve the next
     *             set of email templates within your page size.</p>
     * @public
     */
    NextToken?: string | undefined;
}
/**
 * <p>A list of email addresses that you have verified with Amazon SES under your
 *             Amazon Web Services account.</p>
 * @public
 */
export interface ListVerifiedEmailAddressesResponse {
    /**
     * <p>A list of email addresses that have been verified.</p>
     * @public
     */
    VerifiedEmailAddresses?: string[] | undefined;
}
/**
 * <p> Indicates that the message could not be sent because Amazon SES could not read the MX
 *             record required to use the specified MAIL FROM domain. For information about editing the
 *             custom MAIL FROM domain settings for an identity, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/mail-from-edit.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export declare class MailFromDomainNotVerifiedException extends __BaseException {
    readonly name: "MailFromDomainNotVerifiedException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<MailFromDomainNotVerifiedException, __BaseException>);
}
/**
 * <p>Represents the message to be sent, composed of a subject and a body.</p>
 * @public
 */
export interface Message {
    /**
     * <p>The subject of the message: A short summary of the content, which appears in the
     *             recipient's inbox.</p>
     * @public
     */
    Subject: Content | undefined;
    /**
     * <p>The message body.</p>
     * @public
     */
    Body: Body | undefined;
}
/**
 * <p>Message-related information to include in the Delivery Status Notification (DSN) when
 *             an email that Amazon SES receives on your behalf bounces.</p>
 *          <p>For information about receiving email through Amazon SES, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface MessageDsn {
    /**
     * <p>The reporting MTA that attempted to deliver the message, formatted as specified in
     *                 <a href="https://tools.ietf.org/html/rfc3464">RFC 3464</a>
     *                 (<code>mta-name-type; mta-name</code>). The default value is <code>dns;
     *                 inbound-smtp.[region].amazonaws.com</code>.</p>
     * @public
     */
    ReportingMta: string | undefined;
    /**
     * <p>When the message was received by the reporting mail transfer agent (MTA), in <a href="https://www.ietf.org/rfc/rfc0822.txt">RFC 822</a> date-time format.</p>
     * @public
     */
    ArrivalDate?: Date | undefined;
    /**
     * <p>Additional X-headers to include in the DSN.</p>
     * @public
     */
    ExtensionFields?: ExtensionField[] | undefined;
}
/**
 * <p>Indicates that the action failed, and the message could not be sent. Check the error
 *             stack for more information about what caused the error.</p>
 * @public
 */
export declare class MessageRejected extends __BaseException {
    readonly name: "MessageRejected";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<MessageRejected, __BaseException>);
}
/**
 * <p>Indicates that one or more of the replacement values for the specified template was
 *             not specified. Ensure that the TemplateData object contains references to all of the
 *             replacement tags in the specified template.</p>
 * @public
 */
export declare class MissingRenderingAttributeException extends __BaseException {
    readonly name: "MissingRenderingAttributeException";
    readonly $fault: "client";
    TemplateName?: string | undefined;
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<MissingRenderingAttributeException, __BaseException>);
}
/**
 * @public
 * @enum
 */
export declare const NotificationType: {
    readonly Bounce: "Bounce";
    readonly Complaint: "Complaint";
    readonly Delivery: "Delivery";
};
/**
 * @public
 */
export type NotificationType = (typeof NotificationType)[keyof typeof NotificationType];
/**
 * <p>Indicates that the account has not been granted production access.</p>
 * @public
 */
export declare class ProductionAccessNotGrantedException extends __BaseException {
    readonly name: "ProductionAccessNotGrantedException";
    readonly $fault: "client";
    /**
     * @internal
     */
    constructor(opts: __ExceptionOptionType<ProductionAccessNotGrantedException, __BaseException>);
}
/**
 * <p>A request to modify the delivery options for a configuration set.</p>
 * @public
 */
export interface PutConfigurationSetDeliveryOptionsRequest {
    /**
     * <p>The name of the configuration set.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>Specifies whether messages that use the configuration set are required to use
     *             Transport Layer Security (TLS).</p>
     * @public
     */
    DeliveryOptions?: DeliveryOptions | undefined;
}
/**
 * <p>An HTTP 200 response if the request succeeds, or an error message if the request
 *             fails.</p>
 * @public
 */
export interface PutConfigurationSetDeliveryOptionsResponse {
}
/**
 * <p>Represents a request to add or update a sending authorization policy for an identity.
 *             Sending authorization is an Amazon SES feature that enables you to authorize other senders to
 *             use your identities. For information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface PutIdentityPolicyRequest {
    /**
     * <p>The identity to which that the policy applies. You can specify an identity by using
     *             its name or by using its Amazon Resource Name (ARN). Examples:
     *                 <code>user@example.com</code>, <code>example.com</code>,
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>.</p>
     *          <p>To successfully call this operation, you must own the identity.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>The name of the policy.</p>
     *          <p>The policy name cannot exceed 64 characters and can only include alphanumeric
     *             characters, dashes, and underscores.</p>
     * @public
     */
    PolicyName: string | undefined;
    /**
     * <p>The text of the policy in JSON format. The policy cannot exceed 4 KB.</p>
     *          <p>For information about the syntax of sending authorization policies, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-policies.html">Amazon SES
     *                 Developer Guide</a>. </p>
     * @public
     */
    Policy: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface PutIdentityPolicyResponse {
}
/**
 * <p>Represents the raw data of the message.</p>
 * @public
 */
export interface RawMessage {
    /**
     * <p>The raw data of the message. This data needs to base64-encoded if you are accessing
     *             Amazon SES directly through the HTTPS interface. If you are accessing Amazon SES using an Amazon Web Services
     *             SDK, the SDK takes care of the base 64-encoding for you. In all cases, the client must
     *             ensure that the message format complies with Internet email standards regarding email
     *             header fields, MIME types, and MIME encoding.</p>
     *          <p>The To:, CC:, and BCC: headers in the raw message can contain a group list.</p>
     *          <p>If you are using <code>SendRawEmail</code> with sending authorization, you can include
     *             X-headers in the raw message to specify the "Source," "From," and "Return-Path"
     *             addresses. For more information, see the documentation for <code>SendRawEmail</code>. </p>
     *          <important>
     *             <p>Do not include these X-headers in the DKIM signature, because they are removed by
     *                 Amazon SES before sending the email.</p>
     *          </important>
     *          <p>For more information, go to the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    Data: Uint8Array | undefined;
}
/**
 * <p>Represents a request to reorder the receipt rules within a receipt rule set. You use
 *             receipt rule sets to receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface ReorderReceiptRuleSetRequest {
    /**
     * <p>The name of the receipt rule set to reorder.</p>
     * @public
     */
    RuleSetName: string | undefined;
    /**
     * <p>The specified receipt rule set's receipt rules, in order.</p>
     * @public
     */
    RuleNames: string[] | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface ReorderReceiptRuleSetResponse {
}
/**
 * <p>Represents a request to send a bounce message to the sender of an email you received
 *             through Amazon SES.</p>
 * @public
 */
export interface SendBounceRequest {
    /**
     * <p>The message ID of the message to be bounced.</p>
     * @public
     */
    OriginalMessageId: string | undefined;
    /**
     * <p>The address to use in the "From" header of the bounce message. This must be an
     *             identity that you have verified with Amazon SES.</p>
     * @public
     */
    BounceSender: string | undefined;
    /**
     * <p>Human-readable text for the bounce message to explain the failure. If not specified,
     *             the text is auto-generated based on the bounced recipient information.</p>
     * @public
     */
    Explanation?: string | undefined;
    /**
     * <p>Message-related DSN fields. If not specified, Amazon SES chooses the values.</p>
     * @public
     */
    MessageDsn?: MessageDsn | undefined;
    /**
     * <p>A list of recipients of the bounced message, including the information required to
     *             create the Delivery Status Notifications (DSNs) for the recipients. You must specify at
     *             least one <code>BouncedRecipientInfo</code> in the list.</p>
     * @public
     */
    BouncedRecipientInfoList: BouncedRecipientInfo[] | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to use the
     *             address in the "From" header of the bounce. For more information about sending
     *             authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    BounceSenderArn?: string | undefined;
}
/**
 * <p>Represents a unique message ID.</p>
 * @public
 */
export interface SendBounceResponse {
    /**
     * <p>The message ID of the bounce message.</p>
     * @public
     */
    MessageId?: string | undefined;
}
/**
 * <p>Represents a request to send a templated email to multiple destinations using Amazon SES.
 *             For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-personalized-email-api.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface SendBulkTemplatedEmailRequest {
    /**
     * <p>The email address that is sending the email. This email address must be either
     *             individually verified with Amazon SES, or from a domain that has been verified with Amazon SES.
     *             For information about verifying identities, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html">Amazon SES Developer Guide</a>.</p>
     *          <p>If you are sending on behalf of another user and have been permitted to do so by a
     *             sending authorization policy, then you must also specify the <code>SourceArn</code>
     *             parameter. For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer
     *                 Guide</a>.</p>
     *          <note>
     *             <p>Amazon SES does not support the SMTPUTF8 extension, as described in <a href="https://tools.ietf.org/html/rfc6531">RFC6531</a>. For this reason, the
     *                 email address string must be 7-bit ASCII. If you want to send to or from email
     *                 addresses that contain Unicode characters in the domain part of an address, you must
     *                 encode the domain using Punycode. Punycode is not permitted in the local part of the
     *                 email address (the part before the @ sign) nor in the "friendly from" name. If you
     *                 want to use Unicode characters in the "friendly from" name, you must encode the
     *                 "friendly from" name using MIME encoded-word syntax, as described in <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Sending raw email
     *                     using the Amazon SES API</a>. For more information about Punycode, see <a href="http://tools.ietf.org/html/rfc3492">RFC 3492</a>.</p>
     *          </note>
     * @public
     */
    Source: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to send for
     *             the email address specified in the <code>Source</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to send from <code>user@example.com</code>, then you
     *             would specify the <code>SourceArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>Source</code> to be <code>user@example.com</code>.</p>
     *          <p>For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    SourceArn?: string | undefined;
    /**
     * <p>The reply-to email address(es) for the message. If the recipient replies to the
     *             message, each reply-to address receives the reply.</p>
     * @public
     */
    ReplyToAddresses?: string[] | undefined;
    /**
     * <p>The email address that bounces and complaints are forwarded to when feedback
     *             forwarding is enabled. If the message cannot be delivered to the recipient, then an
     *             error message is returned from the recipient's ISP; this message is forwarded to the
     *             email address specified by the <code>ReturnPath</code> parameter. The
     *                 <code>ReturnPath</code> parameter is never overwritten. This email address must be
     *             either individually verified with Amazon SES, or from a domain that has been verified with
     *             Amazon SES. </p>
     * @public
     */
    ReturnPath?: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to use the
     *             email address specified in the <code>ReturnPath</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to use <code>feedback@example.com</code>, then you
     *             would specify the <code>ReturnPathArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>ReturnPath</code> to be <code>feedback@example.com</code>.</p>
     *          <p>For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    ReturnPathArn?: string | undefined;
    /**
     * <p>The name of the configuration set to use when you send an email using
     *                 <code>SendBulkTemplatedEmail</code>.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * <p>A list of tags, in the form of name/value pairs, to apply to an email that you send to
     *             a destination using <code>SendBulkTemplatedEmail</code>.</p>
     * @public
     */
    DefaultTags?: MessageTag[] | undefined;
    /**
     * <p>The template to use when sending this email.</p>
     * @public
     */
    Template: string | undefined;
    /**
     * <p>The ARN of the template to use when sending this email.</p>
     * @public
     */
    TemplateArn?: string | undefined;
    /**
     * <p>A list of replacement values to apply to the template when replacement data is not
     *             specified in a Destination object. These values act as a default or fallback option when
     *             no other data is available.</p>
     *          <p>The template data is a JSON object, typically consisting of key-value pairs in which
     *             the keys correspond to replacement tags in the email template.</p>
     * @public
     */
    DefaultTemplateData: string | undefined;
    /**
     * <p>One or more <code>Destination</code> objects. All of the recipients in a
     *                 <code>Destination</code> receive the same version of the email. You can specify up
     *             to 50 <code>Destination</code> objects within a <code>Destinations</code> array.</p>
     * @public
     */
    Destinations: BulkEmailDestination[] | undefined;
}
/**
 * @public
 */
export interface SendBulkTemplatedEmailResponse {
    /**
     * <p>One object per intended recipient. Check each response object and retry any messages
     *             with a failure status. (Note that order of responses will be respective to order of
     *             destinations in the request.)Receipt rules enable you to specify which actions </p>
     * @public
     */
    Status: BulkEmailDestinationStatus[] | undefined;
}
/**
 * <p>Represents a request to send a custom verification email to a specified
 *             recipient.</p>
 * @public
 */
export interface SendCustomVerificationEmailRequest {
    /**
     * <p>The email address to verify.</p>
     * @public
     */
    EmailAddress: string | undefined;
    /**
     * <p>The name of the custom verification email template to use when sending the
     *             verification email.</p>
     * @public
     */
    TemplateName: string | undefined;
    /**
     * <p>Name of a configuration set to use when sending the verification email.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
}
/**
 * <p>The response received when attempting to send the custom verification email.</p>
 * @public
 */
export interface SendCustomVerificationEmailResponse {
    /**
     * <p>The unique message identifier returned from the
     *                 <code>SendCustomVerificationEmail</code> operation.</p>
     * @public
     */
    MessageId?: string | undefined;
}
/**
 * <p>Represents a request to send a single formatted email using Amazon SES. For more
 *             information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-formatted.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface SendEmailRequest {
    /**
     * <p>The email address that is sending the email. This email address must be either
     *             individually verified with Amazon SES, or from a domain that has been verified with Amazon SES.
     *             For information about verifying identities, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html">Amazon SES Developer Guide</a>.</p>
     *          <p>If you are sending on behalf of another user and have been permitted to do so by a
     *             sending authorization policy, then you must also specify the <code>SourceArn</code>
     *             parameter. For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer
     *                 Guide</a>.</p>
     *          <note>
     *             <p>Amazon SES does not support the SMTPUTF8 extension, as described in <a href="https://tools.ietf.org/html/rfc6531">RFC6531</a>. For this reason, the
     *                 email address string must be 7-bit ASCII. If you want to send to or from email
     *                 addresses that contain Unicode characters in the domain part of an address, you must
     *                 encode the domain using Punycode. Punycode is not permitted in the local part of the
     *                 email address (the part before the @ sign) nor in the "friendly from" name. If you
     *                 want to use Unicode characters in the "friendly from" name, you must encode the
     *                 "friendly from" name using MIME encoded-word syntax, as described in <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Sending raw email
     *                     using the Amazon SES API</a>. For more information about Punycode, see <a href="http://tools.ietf.org/html/rfc3492">RFC 3492</a>.</p>
     *          </note>
     * @public
     */
    Source: string | undefined;
    /**
     * <p>The destination for this email, composed of To:, CC:, and BCC: fields.</p>
     * @public
     */
    Destination: Destination | undefined;
    /**
     * <p>The message to be sent.</p>
     * @public
     */
    Message: Message | undefined;
    /**
     * <p>The reply-to email address(es) for the message. If the recipient replies to the
     *             message, each reply-to address receives the reply.</p>
     * @public
     */
    ReplyToAddresses?: string[] | undefined;
    /**
     * <p>The email address that bounces and complaints are forwarded to when feedback
     *             forwarding is enabled. If the message cannot be delivered to the recipient, then an
     *             error message is returned from the recipient's ISP; this message is forwarded to the
     *             email address specified by the <code>ReturnPath</code> parameter. The
     *                 <code>ReturnPath</code> parameter is never overwritten. This email address must be
     *             either individually verified with Amazon SES, or from a domain that has been verified with
     *             Amazon SES. </p>
     * @public
     */
    ReturnPath?: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to send for
     *             the email address specified in the <code>Source</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to send from <code>user@example.com</code>, then you
     *             would specify the <code>SourceArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>Source</code> to be <code>user@example.com</code>.</p>
     *          <p>For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    SourceArn?: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to use the
     *             email address specified in the <code>ReturnPath</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to use <code>feedback@example.com</code>, then you
     *             would specify the <code>ReturnPathArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>ReturnPath</code> to be <code>feedback@example.com</code>.</p>
     *          <p>For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    ReturnPathArn?: string | undefined;
    /**
     * <p>A list of tags, in the form of name/value pairs, to apply to an email that you send
     *             using <code>SendEmail</code>. Tags correspond to characteristics of the email that you
     *             define, so that you can publish email sending events.</p>
     * @public
     */
    Tags?: MessageTag[] | undefined;
    /**
     * <p>The name of the configuration set to use when you send an email using
     *                 <code>SendEmail</code>.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
}
/**
 * <p>Represents a unique message ID.</p>
 * @public
 */
export interface SendEmailResponse {
    /**
     * <p>The unique message identifier returned from the <code>SendEmail</code> action. </p>
     * @public
     */
    MessageId: string | undefined;
}
/**
 * <p>Represents a request to send a single raw email using Amazon SES. For more information, see
 *             the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface SendRawEmailRequest {
    /**
     * <p>The identity's email address. If you do not provide a value for this parameter, you
     *             must specify a "From" address in the raw text of the message. (You can also specify
     *             both.)</p>
     *          <note>
     *             <p>Amazon SES does not support the SMTPUTF8 extension, as described in<a href="https://tools.ietf.org/html/rfc6531">RFC6531</a>. For this reason, the
     *                 email address string must be 7-bit ASCII. If you want to send to or from email
     *                 addresses that contain Unicode characters in the domain part of an address, you must
     *                 encode the domain using Punycode. Punycode is not permitted in the local part of the
     *                 email address (the part before the @ sign) nor in the "friendly from" name. If you
     *                 want to use Unicode characters in the "friendly from" name, you must encode the
     *                 "friendly from" name using MIME encoded-word syntax, as described in <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Sending raw email
     *                     using the Amazon SES API</a>. For more information about Punycode, see <a href="http://tools.ietf.org/html/rfc3492">RFC 3492</a>.</p>
     *          </note>
     *          <p>If you specify the <code>Source</code> parameter and have feedback forwarding enabled,
     *             then bounces and complaints are sent to this email address. This takes precedence over
     *             any Return-Path header that you might include in the raw text of the message.</p>
     * @public
     */
    Source?: string | undefined;
    /**
     * <p>A list of destinations for the message, consisting of To:, CC:, and BCC:
     *             addresses.</p>
     * @public
     */
    Destinations?: string[] | undefined;
    /**
     * <p>The raw email message itself. The message has to meet the following criteria:</p>
     *          <ul>
     *             <li>
     *                <p>The message has to contain a header and a body, separated by a blank
     *                     line.</p>
     *             </li>
     *             <li>
     *                <p>All of the required header fields must be present in the message.</p>
     *             </li>
     *             <li>
     *                <p>Each part of a multipart MIME message must be formatted properly.</p>
     *             </li>
     *             <li>
     *                <p>Attachments must be of a content type that Amazon SES supports. For a list on
     *                     unsupported content types, see <a href="https://docs.aws.amazon.com/ses/latest/dg/mime-types.html">Unsupported Attachment Types</a> in
     *                     the <i>Amazon SES Developer Guide</i>.</p>
     *             </li>
     *             <li>
     *                <p>The entire message must be base64-encoded.</p>
     *             </li>
     *             <li>
     *                <p>If any of the MIME parts in your message contain content that is outside of
     *                     the 7-bit ASCII character range, we highly recommend that you encode that
     *                     content. For more information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Sending Raw
     *                         Email</a> in the <i>Amazon SES Developer Guide</i>.</p>
     *             </li>
     *             <li>
     *                <p>Per <a href="https://tools.ietf.org/html/rfc5321#section-4.5.3.1.6">RFC
     *                         5321</a>, the maximum length of each line of text, including the
     *                     <CRLF>, must not exceed 1,000 characters.</p>
     *             </li>
     *          </ul>
     * @public
     */
    RawMessage: RawMessage | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to specify a
     *             particular "From" address in the header of the raw email.</p>
     *          <p>Instead of using this parameter, you can use the X-header <code>X-SES-FROM-ARN</code>
     *             in the raw message of the email. If you use both the <code>FromArn</code> parameter and
     *             the corresponding X-header, Amazon SES uses the value of the <code>FromArn</code>
     *             parameter.</p>
     *          <note>
     *             <p>For information about when to use this parameter, see the description of
     *                     <code>SendRawEmail</code> in this guide, or see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-delegate-sender-tasks-email.html">Amazon SES
     *                     Developer Guide</a>.</p>
     *          </note>
     * @public
     */
    FromArn?: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to send for
     *             the email address specified in the <code>Source</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to send from <code>user@example.com</code>, then you
     *             would specify the <code>SourceArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>Source</code> to be <code>user@example.com</code>.</p>
     *          <p>Instead of using this parameter, you can use the X-header
     *                 <code>X-SES-SOURCE-ARN</code> in the raw message of the email. If you use both the
     *                 <code>SourceArn</code> parameter and the corresponding X-header, Amazon SES uses the
     *             value of the <code>SourceArn</code> parameter.</p>
     *          <note>
     *             <p>For information about when to use this parameter, see the description of
     *                     <code>SendRawEmail</code> in this guide, or see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-delegate-sender-tasks-email.html">Amazon SES
     *                     Developer Guide</a>.</p>
     *          </note>
     * @public
     */
    SourceArn?: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to use the
     *             email address specified in the <code>ReturnPath</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to use <code>feedback@example.com</code>, then you
     *             would specify the <code>ReturnPathArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>ReturnPath</code> to be <code>feedback@example.com</code>.</p>
     *          <p>Instead of using this parameter, you can use the X-header
     *                 <code>X-SES-RETURN-PATH-ARN</code> in the raw message of the email. If you use both
     *             the <code>ReturnPathArn</code> parameter and the corresponding X-header, Amazon SES uses the
     *             value of the <code>ReturnPathArn</code> parameter.</p>
     *          <note>
     *             <p>For information about when to use this parameter, see the description of
     *                     <code>SendRawEmail</code> in this guide, or see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization-delegate-sender-tasks-email.html">Amazon SES
     *                     Developer Guide</a>.</p>
     *          </note>
     * @public
     */
    ReturnPathArn?: string | undefined;
    /**
     * <p>A list of tags, in the form of name/value pairs, to apply to an email that you send
     *             using <code>SendRawEmail</code>. Tags correspond to characteristics of the email that
     *             you define, so that you can publish email sending events.</p>
     * @public
     */
    Tags?: MessageTag[] | undefined;
    /**
     * <p>The name of the configuration set to use when you send an email using
     *                 <code>SendRawEmail</code>.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
}
/**
 * <p>Represents a unique message ID.</p>
 * @public
 */
export interface SendRawEmailResponse {
    /**
     * <p>The unique message identifier returned from the <code>SendRawEmail</code> action.
     *         </p>
     * @public
     */
    MessageId: string | undefined;
}
/**
 * <p>Represents a request to send a templated email using Amazon SES. For more information, see
 *             the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-personalized-email-api.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface SendTemplatedEmailRequest {
    /**
     * <p>The email address that is sending the email. This email address must be either
     *             individually verified with Amazon SES, or from a domain that has been verified with Amazon SES.
     *             For information about verifying identities, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html">Amazon SES Developer Guide</a>.</p>
     *          <p>If you are sending on behalf of another user and have been permitted to do so by a
     *             sending authorization policy, then you must also specify the <code>SourceArn</code>
     *             parameter. For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer
     *                 Guide</a>.</p>
     *          <note>
     *             <p>Amazon SES does not support the SMTPUTF8 extension, as described in <a href="https://tools.ietf.org/html/rfc6531">RFC6531</a>. for this reason, The
     *                 email address string must be 7-bit ASCII. If you want to send to or from email
     *                 addresses that contain Unicode characters in the domain part of an address, you must
     *                 encode the domain using Punycode. Punycode is not permitted in the local part of the
     *                 email address (the part before the @ sign) nor in the "friendly from" name. If you
     *                 want to use Unicode characters in the "friendly from" name, you must encode the
     *                 "friendly from" name using MIME encoded-word syntax, as described in <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-raw.html">Sending raw email
     *                     using the Amazon SES API</a>. For more information about Punycode, see <a href="http://tools.ietf.org/html/rfc3492">RFC 3492</a>.</p>
     *          </note>
     * @public
     */
    Source: string | undefined;
    /**
     * <p>The destination for this email, composed of To:, CC:, and BCC: fields. A Destination
     *             can include up to 50 recipients across these three fields.</p>
     * @public
     */
    Destination: Destination | undefined;
    /**
     * <p>The reply-to email address(es) for the message. If the recipient replies to the
     *             message, each reply-to address receives the reply.</p>
     * @public
     */
    ReplyToAddresses?: string[] | undefined;
    /**
     * <p>The email address that bounces and complaints are forwarded to when feedback
     *             forwarding is enabled. If the message cannot be delivered to the recipient, then an
     *             error message is returned from the recipient's ISP; this message is forwarded to the
     *             email address specified by the <code>ReturnPath</code> parameter. The
     *                 <code>ReturnPath</code> parameter is never overwritten. This email address must be
     *             either individually verified with Amazon SES, or from a domain that has been verified with
     *             Amazon SES. </p>
     * @public
     */
    ReturnPath?: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to send for
     *             the email address specified in the <code>Source</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to send from <code>user@example.com</code>, then you
     *             would specify the <code>SourceArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>Source</code> to be <code>user@example.com</code>.</p>
     *          <p>For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    SourceArn?: string | undefined;
    /**
     * <p>This parameter is used only for sending authorization. It is the ARN of the identity
     *             that is associated with the sending authorization policy that permits you to use the
     *             email address specified in the <code>ReturnPath</code> parameter.</p>
     *          <p>For example, if the owner of <code>example.com</code> (which has ARN
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>) attaches a
     *             policy to it that authorizes you to use <code>feedback@example.com</code>, then you
     *             would specify the <code>ReturnPathArn</code> to be
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>, and the
     *                 <code>ReturnPath</code> to be <code>feedback@example.com</code>.</p>
     *          <p>For more information about sending authorization, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    ReturnPathArn?: string | undefined;
    /**
     * <p>A list of tags, in the form of name/value pairs, to apply to an email that you send
     *             using <code>SendTemplatedEmail</code>. Tags correspond to characteristics of the email
     *             that you define, so that you can publish email sending events.</p>
     * @public
     */
    Tags?: MessageTag[] | undefined;
    /**
     * <p>The name of the configuration set to use when you send an email using
     *                 <code>SendTemplatedEmail</code>.</p>
     * @public
     */
    ConfigurationSetName?: string | undefined;
    /**
     * <p>The template to use when sending this email.</p>
     * @public
     */
    Template: string | undefined;
    /**
     * <p>The ARN of the template to use when sending this email.</p>
     * @public
     */
    TemplateArn?: string | undefined;
    /**
     * <p>A list of replacement values to apply to the template. This parameter is a JSON
     *             object, typically consisting of key-value pairs in which the keys correspond to
     *             replacement tags in the email template.</p>
     * @public
     */
    TemplateData: string | undefined;
}
/**
 * @public
 */
export interface SendTemplatedEmailResponse {
    /**
     * <p>The unique message identifier returned from the <code>SendTemplatedEmail</code>
     *             action. </p>
     * @public
     */
    MessageId: string | undefined;
}
/**
 * <p>Represents a request to set a receipt rule set as the active receipt rule set. You use
 *             receipt rule sets to receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface SetActiveReceiptRuleSetRequest {
    /**
     * <p>The name of the receipt rule set to make active. Setting this value to null disables
     *             all email receiving.</p>
     * @public
     */
    RuleSetName?: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface SetActiveReceiptRuleSetResponse {
}
/**
 * <p>Represents a request to enable or disable Amazon SES Easy DKIM signing for an identity. For
 *             more information about setting up Easy DKIM, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface SetIdentityDkimEnabledRequest {
    /**
     * <p>The identity for which DKIM signing should be enabled or disabled.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>Sets whether DKIM signing is enabled for an identity. Set to <code>true</code> to
     *             enable DKIM signing for this identity; <code>false</code> to disable it. </p>
     * @public
     */
    DkimEnabled: boolean | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface SetIdentityDkimEnabledResponse {
}
/**
 * <p>Represents a request to enable or disable whether Amazon SES forwards you bounce and
 *             complaint notifications through email. For information about email feedback forwarding,
 *             see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications-email.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface SetIdentityFeedbackForwardingEnabledRequest {
    /**
     * <p>The identity for which to set bounce and complaint notification forwarding. Examples:
     *                 <code>user@example.com</code>, <code>example.com</code>.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>Sets whether Amazon SES forwards bounce and complaint notifications as email.
     *                 <code>true</code> specifies that Amazon SES forwards bounce and complaint notifications
     *             as email, in addition to any Amazon SNS topic publishing otherwise specified.
     *                 <code>false</code> specifies that Amazon SES publishes bounce and complaint notifications
     *             only through Amazon SNS. This value can only be set to <code>false</code> when Amazon SNS topics
     *             are set for both <code>Bounce</code> and <code>Complaint</code> notification
     *             types.</p>
     * @public
     */
    ForwardingEnabled: boolean | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface SetIdentityFeedbackForwardingEnabledResponse {
}
/**
 * <p>Represents a request to set whether Amazon SES includes the original email headers in the
 *             Amazon SNS notifications of a specified type. For information about notifications, see the
 *                 <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications-sns.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface SetIdentityHeadersInNotificationsEnabledRequest {
    /**
     * <p>The identity for which to enable or disable headers in notifications. Examples:
     *                 <code>user@example.com</code>, <code>example.com</code>.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>The notification type for which to enable or disable headers in notifications. </p>
     * @public
     */
    NotificationType: NotificationType | undefined;
    /**
     * <p>Sets whether Amazon SES includes the original email headers in Amazon SNS notifications of the
     *             specified notification type. A value of <code>true</code> specifies that Amazon SES includes
     *             headers in notifications, and a value of <code>false</code> specifies that Amazon SES does
     *             not include headers in notifications.</p>
     *          <p>This value can only be set when <code>NotificationType</code> is already set to use a
     *             particular Amazon SNS topic.</p>
     * @public
     */
    Enabled: boolean | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface SetIdentityHeadersInNotificationsEnabledResponse {
}
/**
 * <p>Represents a request to enable or disable the Amazon SES custom MAIL FROM domain setup for
 *             a verified identity. For information about using a custom MAIL FROM domain, see the
 *                 <a href="https://docs.aws.amazon.com/ses/latest/dg/mail-from.html">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface SetIdentityMailFromDomainRequest {
    /**
     * <p>The verified identity.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>The custom MAIL FROM domain for the verified identity to use. The MAIL FROM domain
     *             must 1) be a subdomain of the verified identity, 2) not be used in a "From" address if
     *             the MAIL FROM domain is the destination of email feedback forwarding (for more
     *             information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/mail-from.html">Amazon SES Developer Guide</a>), and 3) not be used to receive emails. A value of
     *                 <code>null</code> disables the custom MAIL FROM setting for the identity.</p>
     * @public
     */
    MailFromDomain?: string | undefined;
    /**
     * <p>The action for Amazon SES to take if it cannot successfully read the required MX record
     *             when you send an email. If you choose <code>UseDefaultValue</code>, Amazon SES uses
     *             amazonses.com (or a subdomain of that) as the MAIL FROM domain. If you choose
     *                 <code>RejectMessage</code>, Amazon SES returns a <code>MailFromDomainNotVerified</code>
     *             error and not send the email.</p>
     *          <p>The action specified in <code>BehaviorOnMXFailure</code> is taken when the custom MAIL
     *             FROM domain setup is in the <code>Pending</code>, <code>Failed</code>, and
     *                 <code>TemporaryFailure</code> states.</p>
     * @public
     */
    BehaviorOnMXFailure?: BehaviorOnMXFailure | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface SetIdentityMailFromDomainResponse {
}
/**
 * <p>Represents a request to specify the Amazon SNS topic to which Amazon SES publishes bounce,
 *             complaint, or delivery notifications for emails sent with that identity as the source.
 *             For information about Amazon SES notifications, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications-sns.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface SetIdentityNotificationTopicRequest {
    /**
     * <p>The identity (email address or domain) for the Amazon SNS topic.</p>
     *          <important>
     *             <p>You can only specify a verified identity for this parameter.</p>
     *          </important>
     *          <p>You can specify an identity by using its name or by using its Amazon Resource Name
     *             (ARN). The following examples are all valid identities: <code>sender@example.com</code>,
     *                 <code>example.com</code>,
     *                 <code>arn:aws:ses:us-east-1:123456789012:identity/example.com</code>.</p>
     * @public
     */
    Identity: string | undefined;
    /**
     * <p>The type of notifications that are published to the specified Amazon SNS topic.</p>
     * @public
     */
    NotificationType: NotificationType | undefined;
    /**
     * <p>The Amazon Resource Name (ARN) of the Amazon SNS topic. If the parameter is omitted from
     *             the request or a null value is passed, <code>SnsTopic</code> is cleared and publishing
     *             is disabled.</p>
     * @public
     */
    SnsTopic?: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface SetIdentityNotificationTopicResponse {
}
/**
 * <p>Represents a request to set the position of a receipt rule in a receipt rule set. You
 *             use receipt rule sets to receive email with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface SetReceiptRulePositionRequest {
    /**
     * <p>The name of the receipt rule set that contains the receipt rule to reposition.</p>
     * @public
     */
    RuleSetName: string | undefined;
    /**
     * <p>The name of the receipt rule to reposition.</p>
     * @public
     */
    RuleName: string | undefined;
    /**
     * <p>The name of the receipt rule after which to place the specified receipt rule.</p>
     * @public
     */
    After?: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface SetReceiptRulePositionResponse {
}
/**
 * @public
 */
export interface TestRenderTemplateRequest {
    /**
     * <p>The name of the template to render.</p>
     * @public
     */
    TemplateName: string | undefined;
    /**
     * <p>A list of replacement values to apply to the template. This parameter is a JSON
     *             object, typically consisting of key-value pairs in which the keys correspond to
     *             replacement tags in the email template.</p>
     * @public
     */
    TemplateData: string | undefined;
}
/**
 * @public
 */
export interface TestRenderTemplateResponse {
    /**
     * <p>The complete MIME message rendered by applying the data in the TemplateData parameter
     *             to the template specified in the TemplateName parameter.</p>
     * @public
     */
    RenderedTemplate?: string | undefined;
}
/**
 * <p>Represents a request to enable or disable the email sending capabilities for your
 *             entire Amazon SES account.</p>
 * @public
 */
export interface UpdateAccountSendingEnabledRequest {
    /**
     * <p>Describes whether email sending is enabled or disabled for your Amazon SES account in the
     *             current Amazon Web Services Region.</p>
     * @public
     */
    Enabled?: boolean | undefined;
}
/**
 * <p>Represents a request to update the event destination of a configuration set.
 *             Configuration sets enable you to publish email sending events. For information about
 *             using configuration sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface UpdateConfigurationSetEventDestinationRequest {
    /**
     * <p>The name of the configuration set that contains the event destination.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>The event destination object.</p>
     * @public
     */
    EventDestination: EventDestination | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface UpdateConfigurationSetEventDestinationResponse {
}
/**
 * <p>Represents a request to modify the reputation metric publishing settings for a
 *             configuration set.</p>
 * @public
 */
export interface UpdateConfigurationSetReputationMetricsEnabledRequest {
    /**
     * <p>The name of the configuration set to update.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>Describes whether or not Amazon SES publishes reputation metrics for the configuration set,
     *             such as bounce and complaint rates, to Amazon CloudWatch.</p>
     * @public
     */
    Enabled: boolean | undefined;
}
/**
 * <p>Represents a request to enable or disable the email sending capabilities for a
 *             specific configuration set.</p>
 * @public
 */
export interface UpdateConfigurationSetSendingEnabledRequest {
    /**
     * <p>The name of the configuration set to update.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>Describes whether email sending is enabled or disabled for the configuration set.
     *         </p>
     * @public
     */
    Enabled: boolean | undefined;
}
/**
 * <p>Represents a request to update the tracking options for a configuration set. </p>
 * @public
 */
export interface UpdateConfigurationSetTrackingOptionsRequest {
    /**
     * <p>The name of the configuration set.</p>
     * @public
     */
    ConfigurationSetName: string | undefined;
    /**
     * <p>A domain that is used to redirect email recipients to an Amazon SES-operated domain. This
     *             domain captures open and click events generated by Amazon SES emails.</p>
     *          <p>For more information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/configure-custom-open-click-domains.html">Configuring Custom
     *                 Domains to Handle Open and Click Tracking</a> in the <i>Amazon SES Developer
     *                 Guide</i>.</p>
     * @public
     */
    TrackingOptions: TrackingOptions | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface UpdateConfigurationSetTrackingOptionsResponse {
}
/**
 * <p>Represents a request to update an existing custom verification email template.</p>
 * @public
 */
export interface UpdateCustomVerificationEmailTemplateRequest {
    /**
     * <p>The name of the custom verification email template to update.</p>
     * @public
     */
    TemplateName: string | undefined;
    /**
     * <p>The email address that the custom verification email is sent from.</p>
     * @public
     */
    FromEmailAddress?: string | undefined;
    /**
     * <p>The subject line of the custom verification email.</p>
     * @public
     */
    TemplateSubject?: string | undefined;
    /**
     * <p>The content of the custom verification email. The total size of the email must be less
     *             than 10 MB. The message body may contain HTML, with some limitations. For more
     *             information, see <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#send-email-verify-address-custom">Custom
     *                 Verification Email Frequently Asked Questions</a> in the <i>Amazon SES
     *                 Developer Guide</i>.</p>
     * @public
     */
    TemplateContent?: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is successfully verified.</p>
     * @public
     */
    SuccessRedirectionURL?: string | undefined;
    /**
     * <p>The URL that the recipient of the verification email is sent to if his or her address
     *             is not successfully verified.</p>
     * @public
     */
    FailureRedirectionURL?: string | undefined;
}
/**
 * <p>Represents a request to update a receipt rule. You use receipt rules to receive email
 *             with Amazon SES. For more information, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html">Amazon SES Developer
 *             Guide</a>.</p>
 * @public
 */
export interface UpdateReceiptRuleRequest {
    /**
     * <p>The name of the receipt rule set that the receipt rule belongs to.</p>
     * @public
     */
    RuleSetName: string | undefined;
    /**
     * <p>A data structure that contains the updated receipt rule information.</p>
     * @public
     */
    Rule: ReceiptRule | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface UpdateReceiptRuleResponse {
}
/**
 * @public
 */
export interface UpdateTemplateRequest {
    /**
     * <p>The content of the email, composed of a subject line and either an HTML part or a
     *             text-only part.</p>
     * @public
     */
    Template: Template | undefined;
}
/**
 * @public
 */
export interface UpdateTemplateResponse {
}
/**
 * <p>Represents a request to generate the CNAME records needed to set up Easy DKIM with
 *             Amazon SES. For more information about setting up Easy DKIM, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html">Amazon SES Developer Guide</a>.</p>
 * @public
 */
export interface VerifyDomainDkimRequest {
    /**
     * <p>The name of the domain to be verified for Easy DKIM signing.</p>
     * @public
     */
    Domain: string | undefined;
}
/**
 * <p>Returns CNAME records that you must publish to the DNS server of your domain to set up
 *             Easy DKIM with Amazon SES.</p>
 * @public
 */
export interface VerifyDomainDkimResponse {
    /**
     * <p>A set of character strings that represent the domain's identity. If the identity is an
     *             email address, the tokens represent the domain of that address.</p>
     *          <p>Using these tokens, you need to create DNS CNAME records that point to DKIM public
     *             keys that are hosted by Amazon SES. Amazon Web Services eventually detects that you've updated your DNS
     *             records. This detection process might take up to 72 hours. After successful detection,
     *             Amazon SES is able to DKIM-sign email originating from that domain. (This only applies to
     *             domain identities, not email address identities.)</p>
     *          <p>For more information about creating DNS records using DKIM tokens, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html">Amazon SES Developer Guide</a>.</p>
     * @public
     */
    DkimTokens: string[] | undefined;
}
/**
 * <p>Represents a request to begin Amazon SES domain verification and to generate the TXT
 *             records that you must publish to the DNS server of your domain to complete the
 *             verification. For information about domain verification, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#verify-domain-procedure">Amazon SES Developer
 *                 Guide</a>.</p>
 * @public
 */
export interface VerifyDomainIdentityRequest {
    /**
     * <p>The domain to be verified.</p>
     * @public
     */
    Domain: string | undefined;
}
/**
 * <p>Returns a TXT record that you must publish to the DNS server of your domain to
 *             complete domain verification with Amazon SES.</p>
 * @public
 */
export interface VerifyDomainIdentityResponse {
    /**
     * <p>A TXT record that you must place in the DNS settings of the domain to complete domain
     *             verification with Amazon SES.</p>
     *          <p>As Amazon SES searches for the TXT record, the domain's verification status is "Pending".
     *             When Amazon SES detects the record, the domain's verification status changes to "Success". If
     *             Amazon SES is unable to detect the record within 72 hours, the domain's verification status
     *             changes to "Failed." In that case, to verify the domain, you must restart the
     *             verification process from the beginning. The domain's verification status also changes
     *             to "Success" when it is DKIM verified.</p>
     * @public
     */
    VerificationToken: string | undefined;
}
/**
 * <p>Represents a request to begin email address verification with Amazon SES. For information
 *             about email address verification, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#verify-email-addresses-procedure">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface VerifyEmailAddressRequest {
    /**
     * <p>The email address to be verified.</p>
     * @public
     */
    EmailAddress: string | undefined;
}
/**
 * <p>Represents a request to begin email address verification with Amazon SES. For information
 *             about email address verification, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#verify-email-addresses-procedure">Amazon SES
 *                 Developer Guide</a>.</p>
 * @public
 */
export interface VerifyEmailIdentityRequest {
    /**
     * <p>The email address to be verified.</p>
     * @public
     */
    EmailAddress: string | undefined;
}
/**
 * <p>An empty element returned on a successful request.</p>
 * @public
 */
export interface VerifyEmailIdentityResponse {
}
