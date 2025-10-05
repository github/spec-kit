import { ExceptionOptionType as __ExceptionOptionType } from "@smithy/smithy-client";
import { SESServiceException as __BaseException } from "./SESServiceException";
export declare class AccountSendingPausedException extends __BaseException {
  readonly name: "AccountSendingPausedException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<AccountSendingPausedException, __BaseException>
  );
}
export interface AddHeaderAction {
  HeaderName: string | undefined;
  HeaderValue: string | undefined;
}
export declare class AlreadyExistsException extends __BaseException {
  readonly name: "AlreadyExistsException";
  readonly $fault: "client";
  Name?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<AlreadyExistsException, __BaseException>
  );
}
export declare const BehaviorOnMXFailure: {
  readonly RejectMessage: "RejectMessage";
  readonly UseDefaultValue: "UseDefaultValue";
};
export type BehaviorOnMXFailure =
  (typeof BehaviorOnMXFailure)[keyof typeof BehaviorOnMXFailure];
export interface Content {
  Data: string | undefined;
  Charset?: string | undefined;
}
export interface Body {
  Text?: Content | undefined;
  Html?: Content | undefined;
}
export interface BounceAction {
  TopicArn?: string | undefined;
  SmtpReplyCode: string | undefined;
  StatusCode?: string | undefined;
  Message: string | undefined;
  Sender: string | undefined;
}
export declare const BounceType: {
  readonly ContentRejected: "ContentRejected";
  readonly DoesNotExist: "DoesNotExist";
  readonly ExceededQuota: "ExceededQuota";
  readonly MessageTooLarge: "MessageTooLarge";
  readonly TemporaryFailure: "TemporaryFailure";
  readonly Undefined: "Undefined";
};
export type BounceType = (typeof BounceType)[keyof typeof BounceType];
export declare const DsnAction: {
  readonly DELAYED: "delayed";
  readonly DELIVERED: "delivered";
  readonly EXPANDED: "expanded";
  readonly FAILED: "failed";
  readonly RELAYED: "relayed";
};
export type DsnAction = (typeof DsnAction)[keyof typeof DsnAction];
export interface ExtensionField {
  Name: string | undefined;
  Value: string | undefined;
}
export interface RecipientDsnFields {
  FinalRecipient?: string | undefined;
  Action: DsnAction | undefined;
  RemoteMta?: string | undefined;
  Status: string | undefined;
  DiagnosticCode?: string | undefined;
  LastAttemptDate?: Date | undefined;
  ExtensionFields?: ExtensionField[] | undefined;
}
export interface BouncedRecipientInfo {
  Recipient: string | undefined;
  RecipientArn?: string | undefined;
  BounceType?: BounceType | undefined;
  RecipientDsnFields?: RecipientDsnFields | undefined;
}
export interface Destination {
  ToAddresses?: string[] | undefined;
  CcAddresses?: string[] | undefined;
  BccAddresses?: string[] | undefined;
}
export interface MessageTag {
  Name: string | undefined;
  Value: string | undefined;
}
export interface BulkEmailDestination {
  Destination: Destination | undefined;
  ReplacementTags?: MessageTag[] | undefined;
  ReplacementTemplateData?: string | undefined;
}
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
export type BulkEmailStatus =
  (typeof BulkEmailStatus)[keyof typeof BulkEmailStatus];
export interface BulkEmailDestinationStatus {
  Status?: BulkEmailStatus | undefined;
  Error?: string | undefined;
  MessageId?: string | undefined;
}
export declare class CannotDeleteException extends __BaseException {
  readonly name: "CannotDeleteException";
  readonly $fault: "client";
  Name?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<CannotDeleteException, __BaseException>
  );
}
export interface CloneReceiptRuleSetRequest {
  RuleSetName: string | undefined;
  OriginalRuleSetName: string | undefined;
}
export interface CloneReceiptRuleSetResponse {}
export declare class LimitExceededException extends __BaseException {
  readonly name: "LimitExceededException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<LimitExceededException, __BaseException>
  );
}
export declare class RuleSetDoesNotExistException extends __BaseException {
  readonly name: "RuleSetDoesNotExistException";
  readonly $fault: "client";
  Name?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<RuleSetDoesNotExistException, __BaseException>
  );
}
export declare const DimensionValueSource: {
  readonly EMAIL_HEADER: "emailHeader";
  readonly LINK_TAG: "linkTag";
  readonly MESSAGE_TAG: "messageTag";
};
export type DimensionValueSource =
  (typeof DimensionValueSource)[keyof typeof DimensionValueSource];
export interface CloudWatchDimensionConfiguration {
  DimensionName: string | undefined;
  DimensionValueSource: DimensionValueSource | undefined;
  DefaultDimensionValue: string | undefined;
}
export interface CloudWatchDestination {
  DimensionConfigurations: CloudWatchDimensionConfiguration[] | undefined;
}
export interface ConfigurationSet {
  Name: string | undefined;
}
export declare class ConfigurationSetAlreadyExistsException extends __BaseException {
  readonly name: "ConfigurationSetAlreadyExistsException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      ConfigurationSetAlreadyExistsException,
      __BaseException
    >
  );
}
export declare const ConfigurationSetAttribute: {
  readonly DELIVERY_OPTIONS: "deliveryOptions";
  readonly EVENT_DESTINATIONS: "eventDestinations";
  readonly REPUTATION_OPTIONS: "reputationOptions";
  readonly TRACKING_OPTIONS: "trackingOptions";
};
export type ConfigurationSetAttribute =
  (typeof ConfigurationSetAttribute)[keyof typeof ConfigurationSetAttribute];
export declare class ConfigurationSetDoesNotExistException extends __BaseException {
  readonly name: "ConfigurationSetDoesNotExistException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      ConfigurationSetDoesNotExistException,
      __BaseException
    >
  );
}
export declare class ConfigurationSetSendingPausedException extends __BaseException {
  readonly name: "ConfigurationSetSendingPausedException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      ConfigurationSetSendingPausedException,
      __BaseException
    >
  );
}
export interface ConnectAction {
  InstanceARN: string | undefined;
  IAMRoleARN: string | undefined;
}
export interface CreateConfigurationSetRequest {
  ConfigurationSet: ConfigurationSet | undefined;
}
export interface CreateConfigurationSetResponse {}
export declare class InvalidConfigurationSetException extends __BaseException {
  readonly name: "InvalidConfigurationSetException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<
      InvalidConfigurationSetException,
      __BaseException
    >
  );
}
export interface KinesisFirehoseDestination {
  IAMRoleARN: string | undefined;
  DeliveryStreamARN: string | undefined;
}
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
export type EventType = (typeof EventType)[keyof typeof EventType];
export interface SNSDestination {
  TopicARN: string | undefined;
}
export interface EventDestination {
  Name: string | undefined;
  Enabled?: boolean | undefined;
  MatchingEventTypes: EventType[] | undefined;
  KinesisFirehoseDestination?: KinesisFirehoseDestination | undefined;
  CloudWatchDestination?: CloudWatchDestination | undefined;
  SNSDestination?: SNSDestination | undefined;
}
export interface CreateConfigurationSetEventDestinationRequest {
  ConfigurationSetName: string | undefined;
  EventDestination: EventDestination | undefined;
}
export interface CreateConfigurationSetEventDestinationResponse {}
export declare class EventDestinationAlreadyExistsException extends __BaseException {
  readonly name: "EventDestinationAlreadyExistsException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  EventDestinationName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      EventDestinationAlreadyExistsException,
      __BaseException
    >
  );
}
export declare class InvalidCloudWatchDestinationException extends __BaseException {
  readonly name: "InvalidCloudWatchDestinationException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  EventDestinationName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      InvalidCloudWatchDestinationException,
      __BaseException
    >
  );
}
export declare class InvalidFirehoseDestinationException extends __BaseException {
  readonly name: "InvalidFirehoseDestinationException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  EventDestinationName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      InvalidFirehoseDestinationException,
      __BaseException
    >
  );
}
export declare class InvalidSNSDestinationException extends __BaseException {
  readonly name: "InvalidSNSDestinationException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  EventDestinationName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<InvalidSNSDestinationException, __BaseException>
  );
}
export interface TrackingOptions {
  CustomRedirectDomain?: string | undefined;
}
export interface CreateConfigurationSetTrackingOptionsRequest {
  ConfigurationSetName: string | undefined;
  TrackingOptions: TrackingOptions | undefined;
}
export interface CreateConfigurationSetTrackingOptionsResponse {}
export declare class InvalidTrackingOptionsException extends __BaseException {
  readonly name: "InvalidTrackingOptionsException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<
      InvalidTrackingOptionsException,
      __BaseException
    >
  );
}
export declare class TrackingOptionsAlreadyExistsException extends __BaseException {
  readonly name: "TrackingOptionsAlreadyExistsException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      TrackingOptionsAlreadyExistsException,
      __BaseException
    >
  );
}
export interface CreateCustomVerificationEmailTemplateRequest {
  TemplateName: string | undefined;
  FromEmailAddress: string | undefined;
  TemplateSubject: string | undefined;
  TemplateContent: string | undefined;
  SuccessRedirectionURL: string | undefined;
  FailureRedirectionURL: string | undefined;
}
export declare class CustomVerificationEmailInvalidContentException extends __BaseException {
  readonly name: "CustomVerificationEmailInvalidContentException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<
      CustomVerificationEmailInvalidContentException,
      __BaseException
    >
  );
}
export declare class CustomVerificationEmailTemplateAlreadyExistsException extends __BaseException {
  readonly name: "CustomVerificationEmailTemplateAlreadyExistsException";
  readonly $fault: "client";
  CustomVerificationEmailTemplateName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      CustomVerificationEmailTemplateAlreadyExistsException,
      __BaseException
    >
  );
}
export declare class FromEmailAddressNotVerifiedException extends __BaseException {
  readonly name: "FromEmailAddressNotVerifiedException";
  readonly $fault: "client";
  FromEmailAddress?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      FromEmailAddressNotVerifiedException,
      __BaseException
    >
  );
}
export declare const ReceiptFilterPolicy: {
  readonly Allow: "Allow";
  readonly Block: "Block";
};
export type ReceiptFilterPolicy =
  (typeof ReceiptFilterPolicy)[keyof typeof ReceiptFilterPolicy];
export interface ReceiptIpFilter {
  Policy: ReceiptFilterPolicy | undefined;
  Cidr: string | undefined;
}
export interface ReceiptFilter {
  Name: string | undefined;
  IpFilter: ReceiptIpFilter | undefined;
}
export interface CreateReceiptFilterRequest {
  Filter: ReceiptFilter | undefined;
}
export interface CreateReceiptFilterResponse {}
export declare const InvocationType: {
  readonly Event: "Event";
  readonly RequestResponse: "RequestResponse";
};
export type InvocationType =
  (typeof InvocationType)[keyof typeof InvocationType];
export interface LambdaAction {
  TopicArn?: string | undefined;
  FunctionArn: string | undefined;
  InvocationType?: InvocationType | undefined;
}
export interface S3Action {
  TopicArn?: string | undefined;
  BucketName: string | undefined;
  ObjectKeyPrefix?: string | undefined;
  KmsKeyArn?: string | undefined;
  IamRoleArn?: string | undefined;
}
export declare const SNSActionEncoding: {
  readonly Base64: "Base64";
  readonly UTF8: "UTF-8";
};
export type SNSActionEncoding =
  (typeof SNSActionEncoding)[keyof typeof SNSActionEncoding];
export interface SNSAction {
  TopicArn: string | undefined;
  Encoding?: SNSActionEncoding | undefined;
}
export declare const StopScope: {
  readonly RULE_SET: "RuleSet";
};
export type StopScope = (typeof StopScope)[keyof typeof StopScope];
export interface StopAction {
  Scope: StopScope | undefined;
  TopicArn?: string | undefined;
}
export interface WorkmailAction {
  TopicArn?: string | undefined;
  OrganizationArn: string | undefined;
}
export interface ReceiptAction {
  S3Action?: S3Action | undefined;
  BounceAction?: BounceAction | undefined;
  WorkmailAction?: WorkmailAction | undefined;
  LambdaAction?: LambdaAction | undefined;
  StopAction?: StopAction | undefined;
  AddHeaderAction?: AddHeaderAction | undefined;
  SNSAction?: SNSAction | undefined;
  ConnectAction?: ConnectAction | undefined;
}
export declare const TlsPolicy: {
  readonly Optional: "Optional";
  readonly Require: "Require";
};
export type TlsPolicy = (typeof TlsPolicy)[keyof typeof TlsPolicy];
export interface ReceiptRule {
  Name: string | undefined;
  Enabled?: boolean | undefined;
  TlsPolicy?: TlsPolicy | undefined;
  Recipients?: string[] | undefined;
  Actions?: ReceiptAction[] | undefined;
  ScanEnabled?: boolean | undefined;
}
export interface CreateReceiptRuleRequest {
  RuleSetName: string | undefined;
  After?: string | undefined;
  Rule: ReceiptRule | undefined;
}
export interface CreateReceiptRuleResponse {}
export declare class InvalidLambdaFunctionException extends __BaseException {
  readonly name: "InvalidLambdaFunctionException";
  readonly $fault: "client";
  FunctionArn?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<InvalidLambdaFunctionException, __BaseException>
  );
}
export declare class InvalidS3ConfigurationException extends __BaseException {
  readonly name: "InvalidS3ConfigurationException";
  readonly $fault: "client";
  Bucket?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      InvalidS3ConfigurationException,
      __BaseException
    >
  );
}
export declare class InvalidSnsTopicException extends __BaseException {
  readonly name: "InvalidSnsTopicException";
  readonly $fault: "client";
  Topic?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<InvalidSnsTopicException, __BaseException>
  );
}
export declare class RuleDoesNotExistException extends __BaseException {
  readonly name: "RuleDoesNotExistException";
  readonly $fault: "client";
  Name?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<RuleDoesNotExistException, __BaseException>
  );
}
export interface CreateReceiptRuleSetRequest {
  RuleSetName: string | undefined;
}
export interface CreateReceiptRuleSetResponse {}
export interface Template {
  TemplateName: string | undefined;
  SubjectPart?: string | undefined;
  TextPart?: string | undefined;
  HtmlPart?: string | undefined;
}
export interface CreateTemplateRequest {
  Template: Template | undefined;
}
export interface CreateTemplateResponse {}
export declare class InvalidTemplateException extends __BaseException {
  readonly name: "InvalidTemplateException";
  readonly $fault: "client";
  TemplateName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<InvalidTemplateException, __BaseException>
  );
}
export declare const CustomMailFromStatus: {
  readonly Failed: "Failed";
  readonly Pending: "Pending";
  readonly Success: "Success";
  readonly TemporaryFailure: "TemporaryFailure";
};
export type CustomMailFromStatus =
  (typeof CustomMailFromStatus)[keyof typeof CustomMailFromStatus];
export interface CustomVerificationEmailTemplate {
  TemplateName?: string | undefined;
  FromEmailAddress?: string | undefined;
  TemplateSubject?: string | undefined;
  SuccessRedirectionURL?: string | undefined;
  FailureRedirectionURL?: string | undefined;
}
export declare class CustomVerificationEmailTemplateDoesNotExistException extends __BaseException {
  readonly name: "CustomVerificationEmailTemplateDoesNotExistException";
  readonly $fault: "client";
  CustomVerificationEmailTemplateName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      CustomVerificationEmailTemplateDoesNotExistException,
      __BaseException
    >
  );
}
export interface DeleteConfigurationSetRequest {
  ConfigurationSetName: string | undefined;
}
export interface DeleteConfigurationSetResponse {}
export interface DeleteConfigurationSetEventDestinationRequest {
  ConfigurationSetName: string | undefined;
  EventDestinationName: string | undefined;
}
export interface DeleteConfigurationSetEventDestinationResponse {}
export declare class EventDestinationDoesNotExistException extends __BaseException {
  readonly name: "EventDestinationDoesNotExistException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  EventDestinationName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      EventDestinationDoesNotExistException,
      __BaseException
    >
  );
}
export interface DeleteConfigurationSetTrackingOptionsRequest {
  ConfigurationSetName: string | undefined;
}
export interface DeleteConfigurationSetTrackingOptionsResponse {}
export declare class TrackingOptionsDoesNotExistException extends __BaseException {
  readonly name: "TrackingOptionsDoesNotExistException";
  readonly $fault: "client";
  ConfigurationSetName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      TrackingOptionsDoesNotExistException,
      __BaseException
    >
  );
}
export interface DeleteCustomVerificationEmailTemplateRequest {
  TemplateName: string | undefined;
}
export interface DeleteIdentityRequest {
  Identity: string | undefined;
}
export interface DeleteIdentityResponse {}
export interface DeleteIdentityPolicyRequest {
  Identity: string | undefined;
  PolicyName: string | undefined;
}
export interface DeleteIdentityPolicyResponse {}
export interface DeleteReceiptFilterRequest {
  FilterName: string | undefined;
}
export interface DeleteReceiptFilterResponse {}
export interface DeleteReceiptRuleRequest {
  RuleSetName: string | undefined;
  RuleName: string | undefined;
}
export interface DeleteReceiptRuleResponse {}
export interface DeleteReceiptRuleSetRequest {
  RuleSetName: string | undefined;
}
export interface DeleteReceiptRuleSetResponse {}
export interface DeleteTemplateRequest {
  TemplateName: string | undefined;
}
export interface DeleteTemplateResponse {}
export interface DeleteVerifiedEmailAddressRequest {
  EmailAddress: string | undefined;
}
export interface DeliveryOptions {
  TlsPolicy?: TlsPolicy | undefined;
}
export interface DescribeActiveReceiptRuleSetRequest {}
export interface ReceiptRuleSetMetadata {
  Name?: string | undefined;
  CreatedTimestamp?: Date | undefined;
}
export interface DescribeActiveReceiptRuleSetResponse {
  Metadata?: ReceiptRuleSetMetadata | undefined;
  Rules?: ReceiptRule[] | undefined;
}
export interface DescribeConfigurationSetRequest {
  ConfigurationSetName: string | undefined;
  ConfigurationSetAttributeNames?: ConfigurationSetAttribute[] | undefined;
}
export interface ReputationOptions {
  SendingEnabled?: boolean | undefined;
  ReputationMetricsEnabled?: boolean | undefined;
  LastFreshStart?: Date | undefined;
}
export interface DescribeConfigurationSetResponse {
  ConfigurationSet?: ConfigurationSet | undefined;
  EventDestinations?: EventDestination[] | undefined;
  TrackingOptions?: TrackingOptions | undefined;
  DeliveryOptions?: DeliveryOptions | undefined;
  ReputationOptions?: ReputationOptions | undefined;
}
export interface DescribeReceiptRuleRequest {
  RuleSetName: string | undefined;
  RuleName: string | undefined;
}
export interface DescribeReceiptRuleResponse {
  Rule?: ReceiptRule | undefined;
}
export interface DescribeReceiptRuleSetRequest {
  RuleSetName: string | undefined;
}
export interface DescribeReceiptRuleSetResponse {
  Metadata?: ReceiptRuleSetMetadata | undefined;
  Rules?: ReceiptRule[] | undefined;
}
export declare const VerificationStatus: {
  readonly Failed: "Failed";
  readonly NotStarted: "NotStarted";
  readonly Pending: "Pending";
  readonly Success: "Success";
  readonly TemporaryFailure: "TemporaryFailure";
};
export type VerificationStatus =
  (typeof VerificationStatus)[keyof typeof VerificationStatus];
export interface IdentityDkimAttributes {
  DkimEnabled: boolean | undefined;
  DkimVerificationStatus: VerificationStatus | undefined;
  DkimTokens?: string[] | undefined;
}
export interface GetAccountSendingEnabledResponse {
  Enabled?: boolean | undefined;
}
export interface GetCustomVerificationEmailTemplateRequest {
  TemplateName: string | undefined;
}
export interface GetCustomVerificationEmailTemplateResponse {
  TemplateName?: string | undefined;
  FromEmailAddress?: string | undefined;
  TemplateSubject?: string | undefined;
  TemplateContent?: string | undefined;
  SuccessRedirectionURL?: string | undefined;
  FailureRedirectionURL?: string | undefined;
}
export interface GetIdentityDkimAttributesRequest {
  Identities: string[] | undefined;
}
export interface GetIdentityDkimAttributesResponse {
  DkimAttributes: Record<string, IdentityDkimAttributes> | undefined;
}
export interface GetIdentityMailFromDomainAttributesRequest {
  Identities: string[] | undefined;
}
export interface IdentityMailFromDomainAttributes {
  MailFromDomain: string | undefined;
  MailFromDomainStatus: CustomMailFromStatus | undefined;
  BehaviorOnMXFailure: BehaviorOnMXFailure | undefined;
}
export interface GetIdentityMailFromDomainAttributesResponse {
  MailFromDomainAttributes:
    | Record<string, IdentityMailFromDomainAttributes>
    | undefined;
}
export interface GetIdentityNotificationAttributesRequest {
  Identities: string[] | undefined;
}
export interface IdentityNotificationAttributes {
  BounceTopic: string | undefined;
  ComplaintTopic: string | undefined;
  DeliveryTopic: string | undefined;
  ForwardingEnabled: boolean | undefined;
  HeadersInBounceNotificationsEnabled?: boolean | undefined;
  HeadersInComplaintNotificationsEnabled?: boolean | undefined;
  HeadersInDeliveryNotificationsEnabled?: boolean | undefined;
}
export interface GetIdentityNotificationAttributesResponse {
  NotificationAttributes:
    | Record<string, IdentityNotificationAttributes>
    | undefined;
}
export interface GetIdentityPoliciesRequest {
  Identity: string | undefined;
  PolicyNames: string[] | undefined;
}
export interface GetIdentityPoliciesResponse {
  Policies: Record<string, string> | undefined;
}
export interface GetIdentityVerificationAttributesRequest {
  Identities: string[] | undefined;
}
export interface IdentityVerificationAttributes {
  VerificationStatus: VerificationStatus | undefined;
  VerificationToken?: string | undefined;
}
export interface GetIdentityVerificationAttributesResponse {
  VerificationAttributes:
    | Record<string, IdentityVerificationAttributes>
    | undefined;
}
export interface GetSendQuotaResponse {
  Max24HourSend?: number | undefined;
  MaxSendRate?: number | undefined;
  SentLast24Hours?: number | undefined;
}
export interface SendDataPoint {
  Timestamp?: Date | undefined;
  DeliveryAttempts?: number | undefined;
  Bounces?: number | undefined;
  Complaints?: number | undefined;
  Rejects?: number | undefined;
}
export interface GetSendStatisticsResponse {
  SendDataPoints?: SendDataPoint[] | undefined;
}
export interface GetTemplateRequest {
  TemplateName: string | undefined;
}
export interface GetTemplateResponse {
  Template?: Template | undefined;
}
export declare class TemplateDoesNotExistException extends __BaseException {
  readonly name: "TemplateDoesNotExistException";
  readonly $fault: "client";
  TemplateName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<TemplateDoesNotExistException, __BaseException>
  );
}
export declare const IdentityType: {
  readonly Domain: "Domain";
  readonly EmailAddress: "EmailAddress";
};
export type IdentityType = (typeof IdentityType)[keyof typeof IdentityType];
export declare class InvalidDeliveryOptionsException extends __BaseException {
  readonly name: "InvalidDeliveryOptionsException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<
      InvalidDeliveryOptionsException,
      __BaseException
    >
  );
}
export declare class InvalidPolicyException extends __BaseException {
  readonly name: "InvalidPolicyException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<InvalidPolicyException, __BaseException>
  );
}
export declare class InvalidRenderingParameterException extends __BaseException {
  readonly name: "InvalidRenderingParameterException";
  readonly $fault: "client";
  TemplateName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      InvalidRenderingParameterException,
      __BaseException
    >
  );
}
export interface ListConfigurationSetsRequest {
  NextToken?: string | undefined;
  MaxItems?: number | undefined;
}
export interface ListConfigurationSetsResponse {
  ConfigurationSets?: ConfigurationSet[] | undefined;
  NextToken?: string | undefined;
}
export interface ListCustomVerificationEmailTemplatesRequest {
  NextToken?: string | undefined;
  MaxResults?: number | undefined;
}
export interface ListCustomVerificationEmailTemplatesResponse {
  CustomVerificationEmailTemplates?:
    | CustomVerificationEmailTemplate[]
    | undefined;
  NextToken?: string | undefined;
}
export interface ListIdentitiesRequest {
  IdentityType?: IdentityType | undefined;
  NextToken?: string | undefined;
  MaxItems?: number | undefined;
}
export interface ListIdentitiesResponse {
  Identities: string[] | undefined;
  NextToken?: string | undefined;
}
export interface ListIdentityPoliciesRequest {
  Identity: string | undefined;
}
export interface ListIdentityPoliciesResponse {
  PolicyNames: string[] | undefined;
}
export interface ListReceiptFiltersRequest {}
export interface ListReceiptFiltersResponse {
  Filters?: ReceiptFilter[] | undefined;
}
export interface ListReceiptRuleSetsRequest {
  NextToken?: string | undefined;
}
export interface ListReceiptRuleSetsResponse {
  RuleSets?: ReceiptRuleSetMetadata[] | undefined;
  NextToken?: string | undefined;
}
export interface ListTemplatesRequest {
  NextToken?: string | undefined;
  MaxItems?: number | undefined;
}
export interface TemplateMetadata {
  Name?: string | undefined;
  CreatedTimestamp?: Date | undefined;
}
export interface ListTemplatesResponse {
  TemplatesMetadata?: TemplateMetadata[] | undefined;
  NextToken?: string | undefined;
}
export interface ListVerifiedEmailAddressesResponse {
  VerifiedEmailAddresses?: string[] | undefined;
}
export declare class MailFromDomainNotVerifiedException extends __BaseException {
  readonly name: "MailFromDomainNotVerifiedException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<
      MailFromDomainNotVerifiedException,
      __BaseException
    >
  );
}
export interface Message {
  Subject: Content | undefined;
  Body: Body | undefined;
}
export interface MessageDsn {
  ReportingMta: string | undefined;
  ArrivalDate?: Date | undefined;
  ExtensionFields?: ExtensionField[] | undefined;
}
export declare class MessageRejected extends __BaseException {
  readonly name: "MessageRejected";
  readonly $fault: "client";
  constructor(opts: __ExceptionOptionType<MessageRejected, __BaseException>);
}
export declare class MissingRenderingAttributeException extends __BaseException {
  readonly name: "MissingRenderingAttributeException";
  readonly $fault: "client";
  TemplateName?: string | undefined;
  constructor(
    opts: __ExceptionOptionType<
      MissingRenderingAttributeException,
      __BaseException
    >
  );
}
export declare const NotificationType: {
  readonly Bounce: "Bounce";
  readonly Complaint: "Complaint";
  readonly Delivery: "Delivery";
};
export type NotificationType =
  (typeof NotificationType)[keyof typeof NotificationType];
export declare class ProductionAccessNotGrantedException extends __BaseException {
  readonly name: "ProductionAccessNotGrantedException";
  readonly $fault: "client";
  constructor(
    opts: __ExceptionOptionType<
      ProductionAccessNotGrantedException,
      __BaseException
    >
  );
}
export interface PutConfigurationSetDeliveryOptionsRequest {
  ConfigurationSetName: string | undefined;
  DeliveryOptions?: DeliveryOptions | undefined;
}
export interface PutConfigurationSetDeliveryOptionsResponse {}
export interface PutIdentityPolicyRequest {
  Identity: string | undefined;
  PolicyName: string | undefined;
  Policy: string | undefined;
}
export interface PutIdentityPolicyResponse {}
export interface RawMessage {
  Data: Uint8Array | undefined;
}
export interface ReorderReceiptRuleSetRequest {
  RuleSetName: string | undefined;
  RuleNames: string[] | undefined;
}
export interface ReorderReceiptRuleSetResponse {}
export interface SendBounceRequest {
  OriginalMessageId: string | undefined;
  BounceSender: string | undefined;
  Explanation?: string | undefined;
  MessageDsn?: MessageDsn | undefined;
  BouncedRecipientInfoList: BouncedRecipientInfo[] | undefined;
  BounceSenderArn?: string | undefined;
}
export interface SendBounceResponse {
  MessageId?: string | undefined;
}
export interface SendBulkTemplatedEmailRequest {
  Source: string | undefined;
  SourceArn?: string | undefined;
  ReplyToAddresses?: string[] | undefined;
  ReturnPath?: string | undefined;
  ReturnPathArn?: string | undefined;
  ConfigurationSetName?: string | undefined;
  DefaultTags?: MessageTag[] | undefined;
  Template: string | undefined;
  TemplateArn?: string | undefined;
  DefaultTemplateData: string | undefined;
  Destinations: BulkEmailDestination[] | undefined;
}
export interface SendBulkTemplatedEmailResponse {
  Status: BulkEmailDestinationStatus[] | undefined;
}
export interface SendCustomVerificationEmailRequest {
  EmailAddress: string | undefined;
  TemplateName: string | undefined;
  ConfigurationSetName?: string | undefined;
}
export interface SendCustomVerificationEmailResponse {
  MessageId?: string | undefined;
}
export interface SendEmailRequest {
  Source: string | undefined;
  Destination: Destination | undefined;
  Message: Message | undefined;
  ReplyToAddresses?: string[] | undefined;
  ReturnPath?: string | undefined;
  SourceArn?: string | undefined;
  ReturnPathArn?: string | undefined;
  Tags?: MessageTag[] | undefined;
  ConfigurationSetName?: string | undefined;
}
export interface SendEmailResponse {
  MessageId: string | undefined;
}
export interface SendRawEmailRequest {
  Source?: string | undefined;
  Destinations?: string[] | undefined;
  RawMessage: RawMessage | undefined;
  FromArn?: string | undefined;
  SourceArn?: string | undefined;
  ReturnPathArn?: string | undefined;
  Tags?: MessageTag[] | undefined;
  ConfigurationSetName?: string | undefined;
}
export interface SendRawEmailResponse {
  MessageId: string | undefined;
}
export interface SendTemplatedEmailRequest {
  Source: string | undefined;
  Destination: Destination | undefined;
  ReplyToAddresses?: string[] | undefined;
  ReturnPath?: string | undefined;
  SourceArn?: string | undefined;
  ReturnPathArn?: string | undefined;
  Tags?: MessageTag[] | undefined;
  ConfigurationSetName?: string | undefined;
  Template: string | undefined;
  TemplateArn?: string | undefined;
  TemplateData: string | undefined;
}
export interface SendTemplatedEmailResponse {
  MessageId: string | undefined;
}
export interface SetActiveReceiptRuleSetRequest {
  RuleSetName?: string | undefined;
}
export interface SetActiveReceiptRuleSetResponse {}
export interface SetIdentityDkimEnabledRequest {
  Identity: string | undefined;
  DkimEnabled: boolean | undefined;
}
export interface SetIdentityDkimEnabledResponse {}
export interface SetIdentityFeedbackForwardingEnabledRequest {
  Identity: string | undefined;
  ForwardingEnabled: boolean | undefined;
}
export interface SetIdentityFeedbackForwardingEnabledResponse {}
export interface SetIdentityHeadersInNotificationsEnabledRequest {
  Identity: string | undefined;
  NotificationType: NotificationType | undefined;
  Enabled: boolean | undefined;
}
export interface SetIdentityHeadersInNotificationsEnabledResponse {}
export interface SetIdentityMailFromDomainRequest {
  Identity: string | undefined;
  MailFromDomain?: string | undefined;
  BehaviorOnMXFailure?: BehaviorOnMXFailure | undefined;
}
export interface SetIdentityMailFromDomainResponse {}
export interface SetIdentityNotificationTopicRequest {
  Identity: string | undefined;
  NotificationType: NotificationType | undefined;
  SnsTopic?: string | undefined;
}
export interface SetIdentityNotificationTopicResponse {}
export interface SetReceiptRulePositionRequest {
  RuleSetName: string | undefined;
  RuleName: string | undefined;
  After?: string | undefined;
}
export interface SetReceiptRulePositionResponse {}
export interface TestRenderTemplateRequest {
  TemplateName: string | undefined;
  TemplateData: string | undefined;
}
export interface TestRenderTemplateResponse {
  RenderedTemplate?: string | undefined;
}
export interface UpdateAccountSendingEnabledRequest {
  Enabled?: boolean | undefined;
}
export interface UpdateConfigurationSetEventDestinationRequest {
  ConfigurationSetName: string | undefined;
  EventDestination: EventDestination | undefined;
}
export interface UpdateConfigurationSetEventDestinationResponse {}
export interface UpdateConfigurationSetReputationMetricsEnabledRequest {
  ConfigurationSetName: string | undefined;
  Enabled: boolean | undefined;
}
export interface UpdateConfigurationSetSendingEnabledRequest {
  ConfigurationSetName: string | undefined;
  Enabled: boolean | undefined;
}
export interface UpdateConfigurationSetTrackingOptionsRequest {
  ConfigurationSetName: string | undefined;
  TrackingOptions: TrackingOptions | undefined;
}
export interface UpdateConfigurationSetTrackingOptionsResponse {}
export interface UpdateCustomVerificationEmailTemplateRequest {
  TemplateName: string | undefined;
  FromEmailAddress?: string | undefined;
  TemplateSubject?: string | undefined;
  TemplateContent?: string | undefined;
  SuccessRedirectionURL?: string | undefined;
  FailureRedirectionURL?: string | undefined;
}
export interface UpdateReceiptRuleRequest {
  RuleSetName: string | undefined;
  Rule: ReceiptRule | undefined;
}
export interface UpdateReceiptRuleResponse {}
export interface UpdateTemplateRequest {
  Template: Template | undefined;
}
export interface UpdateTemplateResponse {}
export interface VerifyDomainDkimRequest {
  Domain: string | undefined;
}
export interface VerifyDomainDkimResponse {
  DkimTokens: string[] | undefined;
}
export interface VerifyDomainIdentityRequest {
  Domain: string | undefined;
}
export interface VerifyDomainIdentityResponse {
  VerificationToken: string | undefined;
}
export interface VerifyEmailAddressRequest {
  EmailAddress: string | undefined;
}
export interface VerifyEmailIdentityRequest {
  EmailAddress: string | undefined;
}
export interface VerifyEmailIdentityResponse {}
