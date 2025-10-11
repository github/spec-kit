import { SESServiceException as __BaseException } from "./SESServiceException";
export class AccountSendingPausedException extends __BaseException {
    name = "AccountSendingPausedException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "AccountSendingPausedException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, AccountSendingPausedException.prototype);
    }
}
export class AlreadyExistsException extends __BaseException {
    name = "AlreadyExistsException";
    $fault = "client";
    Name;
    constructor(opts) {
        super({
            name: "AlreadyExistsException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, AlreadyExistsException.prototype);
        this.Name = opts.Name;
    }
}
export const BehaviorOnMXFailure = {
    RejectMessage: "RejectMessage",
    UseDefaultValue: "UseDefaultValue",
};
export const BounceType = {
    ContentRejected: "ContentRejected",
    DoesNotExist: "DoesNotExist",
    ExceededQuota: "ExceededQuota",
    MessageTooLarge: "MessageTooLarge",
    TemporaryFailure: "TemporaryFailure",
    Undefined: "Undefined",
};
export const DsnAction = {
    DELAYED: "delayed",
    DELIVERED: "delivered",
    EXPANDED: "expanded",
    FAILED: "failed",
    RELAYED: "relayed",
};
export const BulkEmailStatus = {
    AccountDailyQuotaExceeded: "AccountDailyQuotaExceeded",
    AccountSendingPaused: "AccountSendingPaused",
    AccountSuspended: "AccountSuspended",
    AccountThrottled: "AccountThrottled",
    ConfigurationSetDoesNotExist: "ConfigurationSetDoesNotExist",
    ConfigurationSetSendingPaused: "ConfigurationSetSendingPaused",
    Failed: "Failed",
    InvalidParameterValue: "InvalidParameterValue",
    InvalidSendingPoolName: "InvalidSendingPoolName",
    MailFromDomainNotVerified: "MailFromDomainNotVerified",
    MessageRejected: "MessageRejected",
    Success: "Success",
    TemplateDoesNotExist: "TemplateDoesNotExist",
    TransientFailure: "TransientFailure",
};
export class CannotDeleteException extends __BaseException {
    name = "CannotDeleteException";
    $fault = "client";
    Name;
    constructor(opts) {
        super({
            name: "CannotDeleteException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, CannotDeleteException.prototype);
        this.Name = opts.Name;
    }
}
export class LimitExceededException extends __BaseException {
    name = "LimitExceededException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "LimitExceededException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, LimitExceededException.prototype);
    }
}
export class RuleSetDoesNotExistException extends __BaseException {
    name = "RuleSetDoesNotExistException";
    $fault = "client";
    Name;
    constructor(opts) {
        super({
            name: "RuleSetDoesNotExistException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, RuleSetDoesNotExistException.prototype);
        this.Name = opts.Name;
    }
}
export const DimensionValueSource = {
    EMAIL_HEADER: "emailHeader",
    LINK_TAG: "linkTag",
    MESSAGE_TAG: "messageTag",
};
export class ConfigurationSetAlreadyExistsException extends __BaseException {
    name = "ConfigurationSetAlreadyExistsException";
    $fault = "client";
    ConfigurationSetName;
    constructor(opts) {
        super({
            name: "ConfigurationSetAlreadyExistsException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, ConfigurationSetAlreadyExistsException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
    }
}
export const ConfigurationSetAttribute = {
    DELIVERY_OPTIONS: "deliveryOptions",
    EVENT_DESTINATIONS: "eventDestinations",
    REPUTATION_OPTIONS: "reputationOptions",
    TRACKING_OPTIONS: "trackingOptions",
};
export class ConfigurationSetDoesNotExistException extends __BaseException {
    name = "ConfigurationSetDoesNotExistException";
    $fault = "client";
    ConfigurationSetName;
    constructor(opts) {
        super({
            name: "ConfigurationSetDoesNotExistException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, ConfigurationSetDoesNotExistException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
    }
}
export class ConfigurationSetSendingPausedException extends __BaseException {
    name = "ConfigurationSetSendingPausedException";
    $fault = "client";
    ConfigurationSetName;
    constructor(opts) {
        super({
            name: "ConfigurationSetSendingPausedException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, ConfigurationSetSendingPausedException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
    }
}
export class InvalidConfigurationSetException extends __BaseException {
    name = "InvalidConfigurationSetException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "InvalidConfigurationSetException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidConfigurationSetException.prototype);
    }
}
export const EventType = {
    BOUNCE: "bounce",
    CLICK: "click",
    COMPLAINT: "complaint",
    DELIVERY: "delivery",
    OPEN: "open",
    REJECT: "reject",
    RENDERING_FAILURE: "renderingFailure",
    SEND: "send",
};
export class EventDestinationAlreadyExistsException extends __BaseException {
    name = "EventDestinationAlreadyExistsException";
    $fault = "client";
    ConfigurationSetName;
    EventDestinationName;
    constructor(opts) {
        super({
            name: "EventDestinationAlreadyExistsException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, EventDestinationAlreadyExistsException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
        this.EventDestinationName = opts.EventDestinationName;
    }
}
export class InvalidCloudWatchDestinationException extends __BaseException {
    name = "InvalidCloudWatchDestinationException";
    $fault = "client";
    ConfigurationSetName;
    EventDestinationName;
    constructor(opts) {
        super({
            name: "InvalidCloudWatchDestinationException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidCloudWatchDestinationException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
        this.EventDestinationName = opts.EventDestinationName;
    }
}
export class InvalidFirehoseDestinationException extends __BaseException {
    name = "InvalidFirehoseDestinationException";
    $fault = "client";
    ConfigurationSetName;
    EventDestinationName;
    constructor(opts) {
        super({
            name: "InvalidFirehoseDestinationException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidFirehoseDestinationException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
        this.EventDestinationName = opts.EventDestinationName;
    }
}
export class InvalidSNSDestinationException extends __BaseException {
    name = "InvalidSNSDestinationException";
    $fault = "client";
    ConfigurationSetName;
    EventDestinationName;
    constructor(opts) {
        super({
            name: "InvalidSNSDestinationException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidSNSDestinationException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
        this.EventDestinationName = opts.EventDestinationName;
    }
}
export class InvalidTrackingOptionsException extends __BaseException {
    name = "InvalidTrackingOptionsException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "InvalidTrackingOptionsException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidTrackingOptionsException.prototype);
    }
}
export class TrackingOptionsAlreadyExistsException extends __BaseException {
    name = "TrackingOptionsAlreadyExistsException";
    $fault = "client";
    ConfigurationSetName;
    constructor(opts) {
        super({
            name: "TrackingOptionsAlreadyExistsException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, TrackingOptionsAlreadyExistsException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
    }
}
export class CustomVerificationEmailInvalidContentException extends __BaseException {
    name = "CustomVerificationEmailInvalidContentException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "CustomVerificationEmailInvalidContentException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, CustomVerificationEmailInvalidContentException.prototype);
    }
}
export class CustomVerificationEmailTemplateAlreadyExistsException extends __BaseException {
    name = "CustomVerificationEmailTemplateAlreadyExistsException";
    $fault = "client";
    CustomVerificationEmailTemplateName;
    constructor(opts) {
        super({
            name: "CustomVerificationEmailTemplateAlreadyExistsException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, CustomVerificationEmailTemplateAlreadyExistsException.prototype);
        this.CustomVerificationEmailTemplateName = opts.CustomVerificationEmailTemplateName;
    }
}
export class FromEmailAddressNotVerifiedException extends __BaseException {
    name = "FromEmailAddressNotVerifiedException";
    $fault = "client";
    FromEmailAddress;
    constructor(opts) {
        super({
            name: "FromEmailAddressNotVerifiedException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, FromEmailAddressNotVerifiedException.prototype);
        this.FromEmailAddress = opts.FromEmailAddress;
    }
}
export const ReceiptFilterPolicy = {
    Allow: "Allow",
    Block: "Block",
};
export const InvocationType = {
    Event: "Event",
    RequestResponse: "RequestResponse",
};
export const SNSActionEncoding = {
    Base64: "Base64",
    UTF8: "UTF-8",
};
export const StopScope = {
    RULE_SET: "RuleSet",
};
export const TlsPolicy = {
    Optional: "Optional",
    Require: "Require",
};
export class InvalidLambdaFunctionException extends __BaseException {
    name = "InvalidLambdaFunctionException";
    $fault = "client";
    FunctionArn;
    constructor(opts) {
        super({
            name: "InvalidLambdaFunctionException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidLambdaFunctionException.prototype);
        this.FunctionArn = opts.FunctionArn;
    }
}
export class InvalidS3ConfigurationException extends __BaseException {
    name = "InvalidS3ConfigurationException";
    $fault = "client";
    Bucket;
    constructor(opts) {
        super({
            name: "InvalidS3ConfigurationException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidS3ConfigurationException.prototype);
        this.Bucket = opts.Bucket;
    }
}
export class InvalidSnsTopicException extends __BaseException {
    name = "InvalidSnsTopicException";
    $fault = "client";
    Topic;
    constructor(opts) {
        super({
            name: "InvalidSnsTopicException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidSnsTopicException.prototype);
        this.Topic = opts.Topic;
    }
}
export class RuleDoesNotExistException extends __BaseException {
    name = "RuleDoesNotExistException";
    $fault = "client";
    Name;
    constructor(opts) {
        super({
            name: "RuleDoesNotExistException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, RuleDoesNotExistException.prototype);
        this.Name = opts.Name;
    }
}
export class InvalidTemplateException extends __BaseException {
    name = "InvalidTemplateException";
    $fault = "client";
    TemplateName;
    constructor(opts) {
        super({
            name: "InvalidTemplateException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidTemplateException.prototype);
        this.TemplateName = opts.TemplateName;
    }
}
export const CustomMailFromStatus = {
    Failed: "Failed",
    Pending: "Pending",
    Success: "Success",
    TemporaryFailure: "TemporaryFailure",
};
export class CustomVerificationEmailTemplateDoesNotExistException extends __BaseException {
    name = "CustomVerificationEmailTemplateDoesNotExistException";
    $fault = "client";
    CustomVerificationEmailTemplateName;
    constructor(opts) {
        super({
            name: "CustomVerificationEmailTemplateDoesNotExistException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, CustomVerificationEmailTemplateDoesNotExistException.prototype);
        this.CustomVerificationEmailTemplateName = opts.CustomVerificationEmailTemplateName;
    }
}
export class EventDestinationDoesNotExistException extends __BaseException {
    name = "EventDestinationDoesNotExistException";
    $fault = "client";
    ConfigurationSetName;
    EventDestinationName;
    constructor(opts) {
        super({
            name: "EventDestinationDoesNotExistException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, EventDestinationDoesNotExistException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
        this.EventDestinationName = opts.EventDestinationName;
    }
}
export class TrackingOptionsDoesNotExistException extends __BaseException {
    name = "TrackingOptionsDoesNotExistException";
    $fault = "client";
    ConfigurationSetName;
    constructor(opts) {
        super({
            name: "TrackingOptionsDoesNotExistException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, TrackingOptionsDoesNotExistException.prototype);
        this.ConfigurationSetName = opts.ConfigurationSetName;
    }
}
export const VerificationStatus = {
    Failed: "Failed",
    NotStarted: "NotStarted",
    Pending: "Pending",
    Success: "Success",
    TemporaryFailure: "TemporaryFailure",
};
export class TemplateDoesNotExistException extends __BaseException {
    name = "TemplateDoesNotExistException";
    $fault = "client";
    TemplateName;
    constructor(opts) {
        super({
            name: "TemplateDoesNotExistException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, TemplateDoesNotExistException.prototype);
        this.TemplateName = opts.TemplateName;
    }
}
export const IdentityType = {
    Domain: "Domain",
    EmailAddress: "EmailAddress",
};
export class InvalidDeliveryOptionsException extends __BaseException {
    name = "InvalidDeliveryOptionsException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "InvalidDeliveryOptionsException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidDeliveryOptionsException.prototype);
    }
}
export class InvalidPolicyException extends __BaseException {
    name = "InvalidPolicyException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "InvalidPolicyException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidPolicyException.prototype);
    }
}
export class InvalidRenderingParameterException extends __BaseException {
    name = "InvalidRenderingParameterException";
    $fault = "client";
    TemplateName;
    constructor(opts) {
        super({
            name: "InvalidRenderingParameterException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, InvalidRenderingParameterException.prototype);
        this.TemplateName = opts.TemplateName;
    }
}
export class MailFromDomainNotVerifiedException extends __BaseException {
    name = "MailFromDomainNotVerifiedException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "MailFromDomainNotVerifiedException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, MailFromDomainNotVerifiedException.prototype);
    }
}
export class MessageRejected extends __BaseException {
    name = "MessageRejected";
    $fault = "client";
    constructor(opts) {
        super({
            name: "MessageRejected",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, MessageRejected.prototype);
    }
}
export class MissingRenderingAttributeException extends __BaseException {
    name = "MissingRenderingAttributeException";
    $fault = "client";
    TemplateName;
    constructor(opts) {
        super({
            name: "MissingRenderingAttributeException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, MissingRenderingAttributeException.prototype);
        this.TemplateName = opts.TemplateName;
    }
}
export const NotificationType = {
    Bounce: "Bounce",
    Complaint: "Complaint",
    Delivery: "Delivery",
};
export class ProductionAccessNotGrantedException extends __BaseException {
    name = "ProductionAccessNotGrantedException";
    $fault = "client";
    constructor(opts) {
        super({
            name: "ProductionAccessNotGrantedException",
            $fault: "client",
            ...opts,
        });
        Object.setPrototypeOf(this, ProductionAccessNotGrantedException.prototype);
    }
}
