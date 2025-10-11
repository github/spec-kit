import { parseXmlBody as parseBody, parseXmlErrorBody as parseErrorBody } from "@aws-sdk/core";
import { HttpRequest as __HttpRequest } from "@smithy/protocol-http";
import { collectBody, decorateServiceException as __decorateServiceException, expectNonNull as __expectNonNull, expectString as __expectString, extendedEncodeURIComponent as __extendedEncodeURIComponent, getArrayIfSingleItem as __getArrayIfSingleItem, parseBoolean as __parseBoolean, parseRfc3339DateTimeWithOffset as __parseRfc3339DateTimeWithOffset, serializeDateTime as __serializeDateTime, strictParseFloat as __strictParseFloat, strictParseLong as __strictParseLong, withBaseException, } from "@smithy/smithy-client";
import { AccountSendingPausedException, AlreadyExistsException, CannotDeleteException, ConfigurationSetAlreadyExistsException, ConfigurationSetDoesNotExistException, ConfigurationSetSendingPausedException, CustomVerificationEmailInvalidContentException, CustomVerificationEmailTemplateAlreadyExistsException, CustomVerificationEmailTemplateDoesNotExistException, EventDestinationAlreadyExistsException, EventDestinationDoesNotExistException, FromEmailAddressNotVerifiedException, InvalidCloudWatchDestinationException, InvalidConfigurationSetException, InvalidDeliveryOptionsException, InvalidFirehoseDestinationException, InvalidLambdaFunctionException, InvalidPolicyException, InvalidRenderingParameterException, InvalidS3ConfigurationException, InvalidSNSDestinationException, InvalidSnsTopicException, InvalidTemplateException, InvalidTrackingOptionsException, LimitExceededException, MailFromDomainNotVerifiedException, MessageRejected, MissingRenderingAttributeException, ProductionAccessNotGrantedException, RuleDoesNotExistException, RuleSetDoesNotExistException, TemplateDoesNotExistException, TrackingOptionsAlreadyExistsException, TrackingOptionsDoesNotExistException, } from "../models/models_0";
import { SESServiceException as __BaseException } from "../models/SESServiceException";
export const se_CloneReceiptRuleSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CloneReceiptRuleSetRequest(input, context),
        [_A]: _CRRS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateConfigurationSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateConfigurationSetRequest(input, context),
        [_A]: _CCS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateConfigurationSetEventDestinationCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateConfigurationSetEventDestinationRequest(input, context),
        [_A]: _CCSED,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateConfigurationSetTrackingOptionsCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateConfigurationSetTrackingOptionsRequest(input, context),
        [_A]: _CCSTO,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateCustomVerificationEmailTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateCustomVerificationEmailTemplateRequest(input, context),
        [_A]: _CCVET,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateReceiptFilterCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateReceiptFilterRequest(input, context),
        [_A]: _CRF,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateReceiptRuleCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateReceiptRuleRequest(input, context),
        [_A]: _CRR,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateReceiptRuleSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateReceiptRuleSetRequest(input, context),
        [_A]: _CRRSr,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_CreateTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_CreateTemplateRequest(input, context),
        [_A]: _CT,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteConfigurationSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteConfigurationSetRequest(input, context),
        [_A]: _DCS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteConfigurationSetEventDestinationCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteConfigurationSetEventDestinationRequest(input, context),
        [_A]: _DCSED,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteConfigurationSetTrackingOptionsCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteConfigurationSetTrackingOptionsRequest(input, context),
        [_A]: _DCSTO,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteCustomVerificationEmailTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteCustomVerificationEmailTemplateRequest(input, context),
        [_A]: _DCVET,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteIdentityCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteIdentityRequest(input, context),
        [_A]: _DI,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteIdentityPolicyCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteIdentityPolicyRequest(input, context),
        [_A]: _DIP,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteReceiptFilterCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteReceiptFilterRequest(input, context),
        [_A]: _DRF,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteReceiptRuleCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteReceiptRuleRequest(input, context),
        [_A]: _DRR,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteReceiptRuleSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteReceiptRuleSetRequest(input, context),
        [_A]: _DRRS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteTemplateRequest(input, context),
        [_A]: _DT,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DeleteVerifiedEmailAddressCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DeleteVerifiedEmailAddressRequest(input, context),
        [_A]: _DVEA,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DescribeActiveReceiptRuleSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DescribeActiveReceiptRuleSetRequest(input, context),
        [_A]: _DARRS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DescribeConfigurationSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DescribeConfigurationSetRequest(input, context),
        [_A]: _DCSe,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DescribeReceiptRuleCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DescribeReceiptRuleRequest(input, context),
        [_A]: _DRRe,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_DescribeReceiptRuleSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_DescribeReceiptRuleSetRequest(input, context),
        [_A]: _DRRSe,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetAccountSendingEnabledCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    const body = buildFormUrlencodedString({
        [_A]: _GASE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetCustomVerificationEmailTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_GetCustomVerificationEmailTemplateRequest(input, context),
        [_A]: _GCVET,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetIdentityDkimAttributesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_GetIdentityDkimAttributesRequest(input, context),
        [_A]: _GIDA,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetIdentityMailFromDomainAttributesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_GetIdentityMailFromDomainAttributesRequest(input, context),
        [_A]: _GIMFDA,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetIdentityNotificationAttributesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_GetIdentityNotificationAttributesRequest(input, context),
        [_A]: _GINA,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetIdentityPoliciesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_GetIdentityPoliciesRequest(input, context),
        [_A]: _GIP,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetIdentityVerificationAttributesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_GetIdentityVerificationAttributesRequest(input, context),
        [_A]: _GIVA,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetSendQuotaCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    const body = buildFormUrlencodedString({
        [_A]: _GSQ,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetSendStatisticsCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    const body = buildFormUrlencodedString({
        [_A]: _GSS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_GetTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_GetTemplateRequest(input, context),
        [_A]: _GT,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListConfigurationSetsCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ListConfigurationSetsRequest(input, context),
        [_A]: _LCS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListCustomVerificationEmailTemplatesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ListCustomVerificationEmailTemplatesRequest(input, context),
        [_A]: _LCVET,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListIdentitiesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ListIdentitiesRequest(input, context),
        [_A]: _LI,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListIdentityPoliciesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ListIdentityPoliciesRequest(input, context),
        [_A]: _LIP,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListReceiptFiltersCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ListReceiptFiltersRequest(input, context),
        [_A]: _LRF,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListReceiptRuleSetsCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ListReceiptRuleSetsRequest(input, context),
        [_A]: _LRRS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListTemplatesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ListTemplatesRequest(input, context),
        [_A]: _LT,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ListVerifiedEmailAddressesCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    const body = buildFormUrlencodedString({
        [_A]: _LVEA,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_PutConfigurationSetDeliveryOptionsCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_PutConfigurationSetDeliveryOptionsRequest(input, context),
        [_A]: _PCSDO,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_PutIdentityPolicyCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_PutIdentityPolicyRequest(input, context),
        [_A]: _PIP,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_ReorderReceiptRuleSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_ReorderReceiptRuleSetRequest(input, context),
        [_A]: _RRRS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SendBounceCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SendBounceRequest(input, context),
        [_A]: _SB,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SendBulkTemplatedEmailCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SendBulkTemplatedEmailRequest(input, context),
        [_A]: _SBTE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SendCustomVerificationEmailCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SendCustomVerificationEmailRequest(input, context),
        [_A]: _SCVE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SendEmailCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SendEmailRequest(input, context),
        [_A]: _SE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SendRawEmailCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SendRawEmailRequest(input, context),
        [_A]: _SRE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SendTemplatedEmailCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SendTemplatedEmailRequest(input, context),
        [_A]: _STE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SetActiveReceiptRuleSetCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SetActiveReceiptRuleSetRequest(input, context),
        [_A]: _SARRS,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SetIdentityDkimEnabledCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SetIdentityDkimEnabledRequest(input, context),
        [_A]: _SIDE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SetIdentityFeedbackForwardingEnabledCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SetIdentityFeedbackForwardingEnabledRequest(input, context),
        [_A]: _SIFFE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SetIdentityHeadersInNotificationsEnabledCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SetIdentityHeadersInNotificationsEnabledRequest(input, context),
        [_A]: _SIHINE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SetIdentityMailFromDomainCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SetIdentityMailFromDomainRequest(input, context),
        [_A]: _SIMFD,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SetIdentityNotificationTopicCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SetIdentityNotificationTopicRequest(input, context),
        [_A]: _SINT,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_SetReceiptRulePositionCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_SetReceiptRulePositionRequest(input, context),
        [_A]: _SRRP,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_TestRenderTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_TestRenderTemplateRequest(input, context),
        [_A]: _TRT,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateAccountSendingEnabledCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateAccountSendingEnabledRequest(input, context),
        [_A]: _UASE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateConfigurationSetEventDestinationCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateConfigurationSetEventDestinationRequest(input, context),
        [_A]: _UCSED,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateConfigurationSetReputationMetricsEnabledCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateConfigurationSetReputationMetricsEnabledRequest(input, context),
        [_A]: _UCSRME,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateConfigurationSetSendingEnabledCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateConfigurationSetSendingEnabledRequest(input, context),
        [_A]: _UCSSE,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateConfigurationSetTrackingOptionsCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateConfigurationSetTrackingOptionsRequest(input, context),
        [_A]: _UCSTO,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateCustomVerificationEmailTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateCustomVerificationEmailTemplateRequest(input, context),
        [_A]: _UCVET,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateReceiptRuleCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateReceiptRuleRequest(input, context),
        [_A]: _URR,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_UpdateTemplateCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_UpdateTemplateRequest(input, context),
        [_A]: _UT,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_VerifyDomainDkimCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_VerifyDomainDkimRequest(input, context),
        [_A]: _VDD,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_VerifyDomainIdentityCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_VerifyDomainIdentityRequest(input, context),
        [_A]: _VDI,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_VerifyEmailAddressCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_VerifyEmailAddressRequest(input, context),
        [_A]: _VEA,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const se_VerifyEmailIdentityCommand = async (input, context) => {
    const headers = SHARED_HEADERS;
    let body;
    body = buildFormUrlencodedString({
        ...se_VerifyEmailIdentityRequest(input, context),
        [_A]: _VEI,
        [_V]: _,
    });
    return buildHttpRpcRequest(context, headers, "/", undefined, body);
};
export const de_CloneReceiptRuleSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CloneReceiptRuleSetResponse(data.CloneReceiptRuleSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_CreateConfigurationSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CreateConfigurationSetResponse(data.CreateConfigurationSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_CreateConfigurationSetEventDestinationCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CreateConfigurationSetEventDestinationResponse(data.CreateConfigurationSetEventDestinationResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_CreateConfigurationSetTrackingOptionsCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CreateConfigurationSetTrackingOptionsResponse(data.CreateConfigurationSetTrackingOptionsResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_CreateCustomVerificationEmailTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_CreateReceiptFilterCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CreateReceiptFilterResponse(data.CreateReceiptFilterResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_CreateReceiptRuleCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CreateReceiptRuleResponse(data.CreateReceiptRuleResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_CreateReceiptRuleSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CreateReceiptRuleSetResponse(data.CreateReceiptRuleSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_CreateTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_CreateTemplateResponse(data.CreateTemplateResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteConfigurationSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteConfigurationSetResponse(data.DeleteConfigurationSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteConfigurationSetEventDestinationCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteConfigurationSetEventDestinationResponse(data.DeleteConfigurationSetEventDestinationResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteConfigurationSetTrackingOptionsCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteConfigurationSetTrackingOptionsResponse(data.DeleteConfigurationSetTrackingOptionsResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteCustomVerificationEmailTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_DeleteIdentityCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteIdentityResponse(data.DeleteIdentityResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteIdentityPolicyCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteIdentityPolicyResponse(data.DeleteIdentityPolicyResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteReceiptFilterCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteReceiptFilterResponse(data.DeleteReceiptFilterResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteReceiptRuleCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteReceiptRuleResponse(data.DeleteReceiptRuleResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteReceiptRuleSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteReceiptRuleSetResponse(data.DeleteReceiptRuleSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DeleteTemplateResponse(data.DeleteTemplateResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DeleteVerifiedEmailAddressCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_DescribeActiveReceiptRuleSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DescribeActiveReceiptRuleSetResponse(data.DescribeActiveReceiptRuleSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DescribeConfigurationSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DescribeConfigurationSetResponse(data.DescribeConfigurationSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DescribeReceiptRuleCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DescribeReceiptRuleResponse(data.DescribeReceiptRuleResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_DescribeReceiptRuleSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_DescribeReceiptRuleSetResponse(data.DescribeReceiptRuleSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetAccountSendingEnabledCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetAccountSendingEnabledResponse(data.GetAccountSendingEnabledResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetCustomVerificationEmailTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetCustomVerificationEmailTemplateResponse(data.GetCustomVerificationEmailTemplateResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetIdentityDkimAttributesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetIdentityDkimAttributesResponse(data.GetIdentityDkimAttributesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetIdentityMailFromDomainAttributesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetIdentityMailFromDomainAttributesResponse(data.GetIdentityMailFromDomainAttributesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetIdentityNotificationAttributesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetIdentityNotificationAttributesResponse(data.GetIdentityNotificationAttributesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetIdentityPoliciesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetIdentityPoliciesResponse(data.GetIdentityPoliciesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetIdentityVerificationAttributesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetIdentityVerificationAttributesResponse(data.GetIdentityVerificationAttributesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetSendQuotaCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetSendQuotaResponse(data.GetSendQuotaResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetSendStatisticsCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetSendStatisticsResponse(data.GetSendStatisticsResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_GetTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_GetTemplateResponse(data.GetTemplateResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListConfigurationSetsCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListConfigurationSetsResponse(data.ListConfigurationSetsResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListCustomVerificationEmailTemplatesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListCustomVerificationEmailTemplatesResponse(data.ListCustomVerificationEmailTemplatesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListIdentitiesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListIdentitiesResponse(data.ListIdentitiesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListIdentityPoliciesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListIdentityPoliciesResponse(data.ListIdentityPoliciesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListReceiptFiltersCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListReceiptFiltersResponse(data.ListReceiptFiltersResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListReceiptRuleSetsCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListReceiptRuleSetsResponse(data.ListReceiptRuleSetsResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListTemplatesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListTemplatesResponse(data.ListTemplatesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ListVerifiedEmailAddressesCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ListVerifiedEmailAddressesResponse(data.ListVerifiedEmailAddressesResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_PutConfigurationSetDeliveryOptionsCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_PutConfigurationSetDeliveryOptionsResponse(data.PutConfigurationSetDeliveryOptionsResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_PutIdentityPolicyCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_PutIdentityPolicyResponse(data.PutIdentityPolicyResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_ReorderReceiptRuleSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_ReorderReceiptRuleSetResponse(data.ReorderReceiptRuleSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SendBounceCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SendBounceResponse(data.SendBounceResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SendBulkTemplatedEmailCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SendBulkTemplatedEmailResponse(data.SendBulkTemplatedEmailResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SendCustomVerificationEmailCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SendCustomVerificationEmailResponse(data.SendCustomVerificationEmailResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SendEmailCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SendEmailResponse(data.SendEmailResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SendRawEmailCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SendRawEmailResponse(data.SendRawEmailResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SendTemplatedEmailCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SendTemplatedEmailResponse(data.SendTemplatedEmailResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SetActiveReceiptRuleSetCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SetActiveReceiptRuleSetResponse(data.SetActiveReceiptRuleSetResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SetIdentityDkimEnabledCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SetIdentityDkimEnabledResponse(data.SetIdentityDkimEnabledResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SetIdentityFeedbackForwardingEnabledCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SetIdentityFeedbackForwardingEnabledResponse(data.SetIdentityFeedbackForwardingEnabledResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SetIdentityHeadersInNotificationsEnabledCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SetIdentityHeadersInNotificationsEnabledResponse(data.SetIdentityHeadersInNotificationsEnabledResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SetIdentityMailFromDomainCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SetIdentityMailFromDomainResponse(data.SetIdentityMailFromDomainResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SetIdentityNotificationTopicCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SetIdentityNotificationTopicResponse(data.SetIdentityNotificationTopicResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_SetReceiptRulePositionCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_SetReceiptRulePositionResponse(data.SetReceiptRulePositionResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_TestRenderTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_TestRenderTemplateResponse(data.TestRenderTemplateResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_UpdateAccountSendingEnabledCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_UpdateConfigurationSetEventDestinationCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_UpdateConfigurationSetEventDestinationResponse(data.UpdateConfigurationSetEventDestinationResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_UpdateConfigurationSetReputationMetricsEnabledCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_UpdateConfigurationSetSendingEnabledCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_UpdateConfigurationSetTrackingOptionsCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_UpdateConfigurationSetTrackingOptionsResponse(data.UpdateConfigurationSetTrackingOptionsResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_UpdateCustomVerificationEmailTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_UpdateReceiptRuleCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_UpdateReceiptRuleResponse(data.UpdateReceiptRuleResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_UpdateTemplateCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_UpdateTemplateResponse(data.UpdateTemplateResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_VerifyDomainDkimCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_VerifyDomainDkimResponse(data.VerifyDomainDkimResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_VerifyDomainIdentityCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_VerifyDomainIdentityResponse(data.VerifyDomainIdentityResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
export const de_VerifyEmailAddressCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    await collectBody(output.body, context);
    const response = {
        $metadata: deserializeMetadata(output),
    };
    return response;
};
export const de_VerifyEmailIdentityCommand = async (output, context) => {
    if (output.statusCode >= 300) {
        return de_CommandError(output, context);
    }
    const data = await parseBody(output.body, context);
    let contents = {};
    contents = de_VerifyEmailIdentityResponse(data.VerifyEmailIdentityResult, context);
    const response = {
        $metadata: deserializeMetadata(output),
        ...contents,
    };
    return response;
};
const de_CommandError = async (output, context) => {
    const parsedOutput = {
        ...output,
        body: await parseErrorBody(output.body, context),
    };
    const errorCode = loadQueryErrorCode(output, parsedOutput.body);
    switch (errorCode) {
        case "AlreadyExists":
        case "com.amazonaws.ses#AlreadyExistsException":
            throw await de_AlreadyExistsExceptionRes(parsedOutput, context);
        case "LimitExceeded":
        case "com.amazonaws.ses#LimitExceededException":
            throw await de_LimitExceededExceptionRes(parsedOutput, context);
        case "RuleSetDoesNotExist":
        case "com.amazonaws.ses#RuleSetDoesNotExistException":
            throw await de_RuleSetDoesNotExistExceptionRes(parsedOutput, context);
        case "ConfigurationSetAlreadyExists":
        case "com.amazonaws.ses#ConfigurationSetAlreadyExistsException":
            throw await de_ConfigurationSetAlreadyExistsExceptionRes(parsedOutput, context);
        case "InvalidConfigurationSet":
        case "com.amazonaws.ses#InvalidConfigurationSetException":
            throw await de_InvalidConfigurationSetExceptionRes(parsedOutput, context);
        case "ConfigurationSetDoesNotExist":
        case "com.amazonaws.ses#ConfigurationSetDoesNotExistException":
            throw await de_ConfigurationSetDoesNotExistExceptionRes(parsedOutput, context);
        case "EventDestinationAlreadyExists":
        case "com.amazonaws.ses#EventDestinationAlreadyExistsException":
            throw await de_EventDestinationAlreadyExistsExceptionRes(parsedOutput, context);
        case "InvalidCloudWatchDestination":
        case "com.amazonaws.ses#InvalidCloudWatchDestinationException":
            throw await de_InvalidCloudWatchDestinationExceptionRes(parsedOutput, context);
        case "InvalidFirehoseDestination":
        case "com.amazonaws.ses#InvalidFirehoseDestinationException":
            throw await de_InvalidFirehoseDestinationExceptionRes(parsedOutput, context);
        case "InvalidSNSDestination":
        case "com.amazonaws.ses#InvalidSNSDestinationException":
            throw await de_InvalidSNSDestinationExceptionRes(parsedOutput, context);
        case "InvalidTrackingOptions":
        case "com.amazonaws.ses#InvalidTrackingOptionsException":
            throw await de_InvalidTrackingOptionsExceptionRes(parsedOutput, context);
        case "TrackingOptionsAlreadyExistsException":
        case "com.amazonaws.ses#TrackingOptionsAlreadyExistsException":
            throw await de_TrackingOptionsAlreadyExistsExceptionRes(parsedOutput, context);
        case "CustomVerificationEmailInvalidContent":
        case "com.amazonaws.ses#CustomVerificationEmailInvalidContentException":
            throw await de_CustomVerificationEmailInvalidContentExceptionRes(parsedOutput, context);
        case "CustomVerificationEmailTemplateAlreadyExists":
        case "com.amazonaws.ses#CustomVerificationEmailTemplateAlreadyExistsException":
            throw await de_CustomVerificationEmailTemplateAlreadyExistsExceptionRes(parsedOutput, context);
        case "FromEmailAddressNotVerified":
        case "com.amazonaws.ses#FromEmailAddressNotVerifiedException":
            throw await de_FromEmailAddressNotVerifiedExceptionRes(parsedOutput, context);
        case "InvalidLambdaFunction":
        case "com.amazonaws.ses#InvalidLambdaFunctionException":
            throw await de_InvalidLambdaFunctionExceptionRes(parsedOutput, context);
        case "InvalidS3Configuration":
        case "com.amazonaws.ses#InvalidS3ConfigurationException":
            throw await de_InvalidS3ConfigurationExceptionRes(parsedOutput, context);
        case "InvalidSnsTopic":
        case "com.amazonaws.ses#InvalidSnsTopicException":
            throw await de_InvalidSnsTopicExceptionRes(parsedOutput, context);
        case "RuleDoesNotExist":
        case "com.amazonaws.ses#RuleDoesNotExistException":
            throw await de_RuleDoesNotExistExceptionRes(parsedOutput, context);
        case "InvalidTemplate":
        case "com.amazonaws.ses#InvalidTemplateException":
            throw await de_InvalidTemplateExceptionRes(parsedOutput, context);
        case "EventDestinationDoesNotExist":
        case "com.amazonaws.ses#EventDestinationDoesNotExistException":
            throw await de_EventDestinationDoesNotExistExceptionRes(parsedOutput, context);
        case "TrackingOptionsDoesNotExistException":
        case "com.amazonaws.ses#TrackingOptionsDoesNotExistException":
            throw await de_TrackingOptionsDoesNotExistExceptionRes(parsedOutput, context);
        case "CannotDelete":
        case "com.amazonaws.ses#CannotDeleteException":
            throw await de_CannotDeleteExceptionRes(parsedOutput, context);
        case "CustomVerificationEmailTemplateDoesNotExist":
        case "com.amazonaws.ses#CustomVerificationEmailTemplateDoesNotExistException":
            throw await de_CustomVerificationEmailTemplateDoesNotExistExceptionRes(parsedOutput, context);
        case "TemplateDoesNotExist":
        case "com.amazonaws.ses#TemplateDoesNotExistException":
            throw await de_TemplateDoesNotExistExceptionRes(parsedOutput, context);
        case "InvalidDeliveryOptions":
        case "com.amazonaws.ses#InvalidDeliveryOptionsException":
            throw await de_InvalidDeliveryOptionsExceptionRes(parsedOutput, context);
        case "InvalidPolicy":
        case "com.amazonaws.ses#InvalidPolicyException":
            throw await de_InvalidPolicyExceptionRes(parsedOutput, context);
        case "MessageRejected":
        case "com.amazonaws.ses#MessageRejected":
            throw await de_MessageRejectedRes(parsedOutput, context);
        case "AccountSendingPausedException":
        case "com.amazonaws.ses#AccountSendingPausedException":
            throw await de_AccountSendingPausedExceptionRes(parsedOutput, context);
        case "ConfigurationSetSendingPausedException":
        case "com.amazonaws.ses#ConfigurationSetSendingPausedException":
            throw await de_ConfigurationSetSendingPausedExceptionRes(parsedOutput, context);
        case "MailFromDomainNotVerifiedException":
        case "com.amazonaws.ses#MailFromDomainNotVerifiedException":
            throw await de_MailFromDomainNotVerifiedExceptionRes(parsedOutput, context);
        case "ProductionAccessNotGranted":
        case "com.amazonaws.ses#ProductionAccessNotGrantedException":
            throw await de_ProductionAccessNotGrantedExceptionRes(parsedOutput, context);
        case "InvalidRenderingParameter":
        case "com.amazonaws.ses#InvalidRenderingParameterException":
            throw await de_InvalidRenderingParameterExceptionRes(parsedOutput, context);
        case "MissingRenderingAttribute":
        case "com.amazonaws.ses#MissingRenderingAttributeException":
            throw await de_MissingRenderingAttributeExceptionRes(parsedOutput, context);
        default:
            const parsedBody = parsedOutput.body;
            return throwDefaultError({
                output,
                parsedBody: parsedBody.Error,
                errorCode,
            });
    }
};
const de_AccountSendingPausedExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_AccountSendingPausedException(body.Error, context);
    const exception = new AccountSendingPausedException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_AlreadyExistsExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_AlreadyExistsException(body.Error, context);
    const exception = new AlreadyExistsException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_CannotDeleteExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_CannotDeleteException(body.Error, context);
    const exception = new CannotDeleteException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_ConfigurationSetAlreadyExistsExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_ConfigurationSetAlreadyExistsException(body.Error, context);
    const exception = new ConfigurationSetAlreadyExistsException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_ConfigurationSetDoesNotExistExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_ConfigurationSetDoesNotExistException(body.Error, context);
    const exception = new ConfigurationSetDoesNotExistException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_ConfigurationSetSendingPausedExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_ConfigurationSetSendingPausedException(body.Error, context);
    const exception = new ConfigurationSetSendingPausedException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_CustomVerificationEmailInvalidContentExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_CustomVerificationEmailInvalidContentException(body.Error, context);
    const exception = new CustomVerificationEmailInvalidContentException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_CustomVerificationEmailTemplateAlreadyExistsExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_CustomVerificationEmailTemplateAlreadyExistsException(body.Error, context);
    const exception = new CustomVerificationEmailTemplateAlreadyExistsException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_CustomVerificationEmailTemplateDoesNotExistExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_CustomVerificationEmailTemplateDoesNotExistException(body.Error, context);
    const exception = new CustomVerificationEmailTemplateDoesNotExistException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_EventDestinationAlreadyExistsExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_EventDestinationAlreadyExistsException(body.Error, context);
    const exception = new EventDestinationAlreadyExistsException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_EventDestinationDoesNotExistExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_EventDestinationDoesNotExistException(body.Error, context);
    const exception = new EventDestinationDoesNotExistException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_FromEmailAddressNotVerifiedExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_FromEmailAddressNotVerifiedException(body.Error, context);
    const exception = new FromEmailAddressNotVerifiedException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidCloudWatchDestinationExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidCloudWatchDestinationException(body.Error, context);
    const exception = new InvalidCloudWatchDestinationException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidConfigurationSetExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidConfigurationSetException(body.Error, context);
    const exception = new InvalidConfigurationSetException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidDeliveryOptionsExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidDeliveryOptionsException(body.Error, context);
    const exception = new InvalidDeliveryOptionsException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidFirehoseDestinationExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidFirehoseDestinationException(body.Error, context);
    const exception = new InvalidFirehoseDestinationException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidLambdaFunctionExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidLambdaFunctionException(body.Error, context);
    const exception = new InvalidLambdaFunctionException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidPolicyExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidPolicyException(body.Error, context);
    const exception = new InvalidPolicyException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidRenderingParameterExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidRenderingParameterException(body.Error, context);
    const exception = new InvalidRenderingParameterException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidS3ConfigurationExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidS3ConfigurationException(body.Error, context);
    const exception = new InvalidS3ConfigurationException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidSNSDestinationExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidSNSDestinationException(body.Error, context);
    const exception = new InvalidSNSDestinationException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidSnsTopicExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidSnsTopicException(body.Error, context);
    const exception = new InvalidSnsTopicException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidTemplateExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidTemplateException(body.Error, context);
    const exception = new InvalidTemplateException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_InvalidTrackingOptionsExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_InvalidTrackingOptionsException(body.Error, context);
    const exception = new InvalidTrackingOptionsException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_LimitExceededExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_LimitExceededException(body.Error, context);
    const exception = new LimitExceededException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_MailFromDomainNotVerifiedExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_MailFromDomainNotVerifiedException(body.Error, context);
    const exception = new MailFromDomainNotVerifiedException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_MessageRejectedRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_MessageRejected(body.Error, context);
    const exception = new MessageRejected({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_MissingRenderingAttributeExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_MissingRenderingAttributeException(body.Error, context);
    const exception = new MissingRenderingAttributeException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_ProductionAccessNotGrantedExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_ProductionAccessNotGrantedException(body.Error, context);
    const exception = new ProductionAccessNotGrantedException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_RuleDoesNotExistExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_RuleDoesNotExistException(body.Error, context);
    const exception = new RuleDoesNotExistException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_RuleSetDoesNotExistExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_RuleSetDoesNotExistException(body.Error, context);
    const exception = new RuleSetDoesNotExistException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_TemplateDoesNotExistExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_TemplateDoesNotExistException(body.Error, context);
    const exception = new TemplateDoesNotExistException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_TrackingOptionsAlreadyExistsExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_TrackingOptionsAlreadyExistsException(body.Error, context);
    const exception = new TrackingOptionsAlreadyExistsException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const de_TrackingOptionsDoesNotExistExceptionRes = async (parsedOutput, context) => {
    const body = parsedOutput.body;
    const deserialized = de_TrackingOptionsDoesNotExistException(body.Error, context);
    const exception = new TrackingOptionsDoesNotExistException({
        $metadata: deserializeMetadata(parsedOutput),
        ...deserialized,
    });
    return __decorateServiceException(exception, body);
};
const se_AddHeaderAction = (input, context) => {
    const entries = {};
    if (input[_HN] != null) {
        entries[_HN] = input[_HN];
    }
    if (input[_HV] != null) {
        entries[_HV] = input[_HV];
    }
    return entries;
};
const se_AddressList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        entries[`member.${counter}`] = entry;
        counter++;
    }
    return entries;
};
const se_Body = (input, context) => {
    const entries = {};
    if (input[_T] != null) {
        const memberEntries = se_Content(input[_T], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Text.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_H] != null) {
        const memberEntries = se_Content(input[_H], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Html.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_BounceAction = (input, context) => {
    const entries = {};
    if (input[_TA] != null) {
        entries[_TA] = input[_TA];
    }
    if (input[_SRC] != null) {
        entries[_SRC] = input[_SRC];
    }
    if (input[_SC] != null) {
        entries[_SC] = input[_SC];
    }
    if (input[_M] != null) {
        entries[_M] = input[_M];
    }
    if (input[_S] != null) {
        entries[_S] = input[_S];
    }
    return entries;
};
const se_BouncedRecipientInfo = (input, context) => {
    const entries = {};
    if (input[_R] != null) {
        entries[_R] = input[_R];
    }
    if (input[_RA] != null) {
        entries[_RA] = input[_RA];
    }
    if (input[_BT] != null) {
        entries[_BT] = input[_BT];
    }
    if (input[_RDF] != null) {
        const memberEntries = se_RecipientDsnFields(input[_RDF], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `RecipientDsnFields.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_BouncedRecipientInfoList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        const memberEntries = se_BouncedRecipientInfo(entry, context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            entries[`member.${counter}.${key}`] = value;
        });
        counter++;
    }
    return entries;
};
const se_BulkEmailDestination = (input, context) => {
    const entries = {};
    if (input[_D] != null) {
        const memberEntries = se_Destination(input[_D], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Destination.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RT] != null) {
        const memberEntries = se_MessageTagList(input[_RT], context);
        if (input[_RT]?.length === 0) {
            entries.ReplacementTags = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ReplacementTags.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RTD] != null) {
        entries[_RTD] = input[_RTD];
    }
    return entries;
};
const se_BulkEmailDestinationList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        const memberEntries = se_BulkEmailDestination(entry, context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            entries[`member.${counter}.${key}`] = value;
        });
        counter++;
    }
    return entries;
};
const se_CloneReceiptRuleSetRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    if (input[_ORSN] != null) {
        entries[_ORSN] = input[_ORSN];
    }
    return entries;
};
const se_CloudWatchDestination = (input, context) => {
    const entries = {};
    if (input[_DC] != null) {
        const memberEntries = se_CloudWatchDimensionConfigurations(input[_DC], context);
        if (input[_DC]?.length === 0) {
            entries.DimensionConfigurations = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `DimensionConfigurations.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_CloudWatchDimensionConfiguration = (input, context) => {
    const entries = {};
    if (input[_DN] != null) {
        entries[_DN] = input[_DN];
    }
    if (input[_DVS] != null) {
        entries[_DVS] = input[_DVS];
    }
    if (input[_DDV] != null) {
        entries[_DDV] = input[_DDV];
    }
    return entries;
};
const se_CloudWatchDimensionConfigurations = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        const memberEntries = se_CloudWatchDimensionConfiguration(entry, context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            entries[`member.${counter}.${key}`] = value;
        });
        counter++;
    }
    return entries;
};
const se_ConfigurationSet = (input, context) => {
    const entries = {};
    if (input[_N] != null) {
        entries[_N] = input[_N];
    }
    return entries;
};
const se_ConfigurationSetAttributeList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        entries[`member.${counter}`] = entry;
        counter++;
    }
    return entries;
};
const se_ConnectAction = (input, context) => {
    const entries = {};
    if (input[_IARN] != null) {
        entries[_IARN] = input[_IARN];
    }
    if (input[_IAMRARN] != null) {
        entries[_IAMRARN] = input[_IAMRARN];
    }
    return entries;
};
const se_Content = (input, context) => {
    const entries = {};
    if (input[_Da] != null) {
        entries[_Da] = input[_Da];
    }
    if (input[_C] != null) {
        entries[_C] = input[_C];
    }
    return entries;
};
const se_CreateConfigurationSetEventDestinationRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_ED] != null) {
        const memberEntries = se_EventDestination(input[_ED], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `EventDestination.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_CreateConfigurationSetRequest = (input, context) => {
    const entries = {};
    if (input[_CS] != null) {
        const memberEntries = se_ConfigurationSet(input[_CS], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ConfigurationSet.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_CreateConfigurationSetTrackingOptionsRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_TO] != null) {
        const memberEntries = se_TrackingOptions(input[_TO], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `TrackingOptions.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_CreateCustomVerificationEmailTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    if (input[_FEA] != null) {
        entries[_FEA] = input[_FEA];
    }
    if (input[_TS] != null) {
        entries[_TS] = input[_TS];
    }
    if (input[_TC] != null) {
        entries[_TC] = input[_TC];
    }
    if (input[_SRURL] != null) {
        entries[_SRURL] = input[_SRURL];
    }
    if (input[_FRURL] != null) {
        entries[_FRURL] = input[_FRURL];
    }
    return entries;
};
const se_CreateReceiptFilterRequest = (input, context) => {
    const entries = {};
    if (input[_F] != null) {
        const memberEntries = se_ReceiptFilter(input[_F], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Filter.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_CreateReceiptRuleRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    if (input[_Af] != null) {
        entries[_Af] = input[_Af];
    }
    if (input[_Ru] != null) {
        const memberEntries = se_ReceiptRule(input[_Ru], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Rule.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_CreateReceiptRuleSetRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    return entries;
};
const se_CreateTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_Te] != null) {
        const memberEntries = se_Template(input[_Te], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Template.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_DeleteConfigurationSetEventDestinationRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_EDN] != null) {
        entries[_EDN] = input[_EDN];
    }
    return entries;
};
const se_DeleteConfigurationSetRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    return entries;
};
const se_DeleteConfigurationSetTrackingOptionsRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    return entries;
};
const se_DeleteCustomVerificationEmailTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    return entries;
};
const se_DeleteIdentityPolicyRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_PN] != null) {
        entries[_PN] = input[_PN];
    }
    return entries;
};
const se_DeleteIdentityRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    return entries;
};
const se_DeleteReceiptFilterRequest = (input, context) => {
    const entries = {};
    if (input[_FN] != null) {
        entries[_FN] = input[_FN];
    }
    return entries;
};
const se_DeleteReceiptRuleRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    if (input[_RN] != null) {
        entries[_RN] = input[_RN];
    }
    return entries;
};
const se_DeleteReceiptRuleSetRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    return entries;
};
const se_DeleteTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    return entries;
};
const se_DeleteVerifiedEmailAddressRequest = (input, context) => {
    const entries = {};
    if (input[_EA] != null) {
        entries[_EA] = input[_EA];
    }
    return entries;
};
const se_DeliveryOptions = (input, context) => {
    const entries = {};
    if (input[_TP] != null) {
        entries[_TP] = input[_TP];
    }
    return entries;
};
const se_DescribeActiveReceiptRuleSetRequest = (input, context) => {
    const entries = {};
    return entries;
};
const se_DescribeConfigurationSetRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_CSAN] != null) {
        const memberEntries = se_ConfigurationSetAttributeList(input[_CSAN], context);
        if (input[_CSAN]?.length === 0) {
            entries.ConfigurationSetAttributeNames = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ConfigurationSetAttributeNames.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_DescribeReceiptRuleRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    if (input[_RN] != null) {
        entries[_RN] = input[_RN];
    }
    return entries;
};
const se_DescribeReceiptRuleSetRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    return entries;
};
const se_Destination = (input, context) => {
    const entries = {};
    if (input[_TAo] != null) {
        const memberEntries = se_AddressList(input[_TAo], context);
        if (input[_TAo]?.length === 0) {
            entries.ToAddresses = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ToAddresses.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_CA] != null) {
        const memberEntries = se_AddressList(input[_CA], context);
        if (input[_CA]?.length === 0) {
            entries.CcAddresses = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `CcAddresses.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_BA] != null) {
        const memberEntries = se_AddressList(input[_BA], context);
        if (input[_BA]?.length === 0) {
            entries.BccAddresses = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `BccAddresses.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_EventDestination = (input, context) => {
    const entries = {};
    if (input[_N] != null) {
        entries[_N] = input[_N];
    }
    if (input[_E] != null) {
        entries[_E] = input[_E];
    }
    if (input[_MET] != null) {
        const memberEntries = se_EventTypes(input[_MET], context);
        if (input[_MET]?.length === 0) {
            entries.MatchingEventTypes = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `MatchingEventTypes.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_KFD] != null) {
        const memberEntries = se_KinesisFirehoseDestination(input[_KFD], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `KinesisFirehoseDestination.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_CWD] != null) {
        const memberEntries = se_CloudWatchDestination(input[_CWD], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `CloudWatchDestination.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_SNSD] != null) {
        const memberEntries = se_SNSDestination(input[_SNSD], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `SNSDestination.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_EventTypes = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        entries[`member.${counter}`] = entry;
        counter++;
    }
    return entries;
};
const se_ExtensionField = (input, context) => {
    const entries = {};
    if (input[_N] != null) {
        entries[_N] = input[_N];
    }
    if (input[_Va] != null) {
        entries[_Va] = input[_Va];
    }
    return entries;
};
const se_ExtensionFieldList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        const memberEntries = se_ExtensionField(entry, context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            entries[`member.${counter}.${key}`] = value;
        });
        counter++;
    }
    return entries;
};
const se_GetCustomVerificationEmailTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    return entries;
};
const se_GetIdentityDkimAttributesRequest = (input, context) => {
    const entries = {};
    if (input[_Id] != null) {
        const memberEntries = se_IdentityList(input[_Id], context);
        if (input[_Id]?.length === 0) {
            entries.Identities = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Identities.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_GetIdentityMailFromDomainAttributesRequest = (input, context) => {
    const entries = {};
    if (input[_Id] != null) {
        const memberEntries = se_IdentityList(input[_Id], context);
        if (input[_Id]?.length === 0) {
            entries.Identities = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Identities.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_GetIdentityNotificationAttributesRequest = (input, context) => {
    const entries = {};
    if (input[_Id] != null) {
        const memberEntries = se_IdentityList(input[_Id], context);
        if (input[_Id]?.length === 0) {
            entries.Identities = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Identities.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_GetIdentityPoliciesRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_PNo] != null) {
        const memberEntries = se_PolicyNameList(input[_PNo], context);
        if (input[_PNo]?.length === 0) {
            entries.PolicyNames = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `PolicyNames.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_GetIdentityVerificationAttributesRequest = (input, context) => {
    const entries = {};
    if (input[_Id] != null) {
        const memberEntries = se_IdentityList(input[_Id], context);
        if (input[_Id]?.length === 0) {
            entries.Identities = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Identities.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_GetTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    return entries;
};
const se_IdentityList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        entries[`member.${counter}`] = entry;
        counter++;
    }
    return entries;
};
const se_KinesisFirehoseDestination = (input, context) => {
    const entries = {};
    if (input[_IAMRARN] != null) {
        entries[_IAMRARN] = input[_IAMRARN];
    }
    if (input[_DSARN] != null) {
        entries[_DSARN] = input[_DSARN];
    }
    return entries;
};
const se_LambdaAction = (input, context) => {
    const entries = {};
    if (input[_TA] != null) {
        entries[_TA] = input[_TA];
    }
    if (input[_FA] != null) {
        entries[_FA] = input[_FA];
    }
    if (input[_IT] != null) {
        entries[_IT] = input[_IT];
    }
    return entries;
};
const se_ListConfigurationSetsRequest = (input, context) => {
    const entries = {};
    if (input[_NT] != null) {
        entries[_NT] = input[_NT];
    }
    if (input[_MI] != null) {
        entries[_MI] = input[_MI];
    }
    return entries;
};
const se_ListCustomVerificationEmailTemplatesRequest = (input, context) => {
    const entries = {};
    if (input[_NT] != null) {
        entries[_NT] = input[_NT];
    }
    if (input[_MR] != null) {
        entries[_MR] = input[_MR];
    }
    return entries;
};
const se_ListIdentitiesRequest = (input, context) => {
    const entries = {};
    if (input[_ITd] != null) {
        entries[_ITd] = input[_ITd];
    }
    if (input[_NT] != null) {
        entries[_NT] = input[_NT];
    }
    if (input[_MI] != null) {
        entries[_MI] = input[_MI];
    }
    return entries;
};
const se_ListIdentityPoliciesRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    return entries;
};
const se_ListReceiptFiltersRequest = (input, context) => {
    const entries = {};
    return entries;
};
const se_ListReceiptRuleSetsRequest = (input, context) => {
    const entries = {};
    if (input[_NT] != null) {
        entries[_NT] = input[_NT];
    }
    return entries;
};
const se_ListTemplatesRequest = (input, context) => {
    const entries = {};
    if (input[_NT] != null) {
        entries[_NT] = input[_NT];
    }
    if (input[_MI] != null) {
        entries[_MI] = input[_MI];
    }
    return entries;
};
const se_Message = (input, context) => {
    const entries = {};
    if (input[_Su] != null) {
        const memberEntries = se_Content(input[_Su], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Subject.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_B] != null) {
        const memberEntries = se_Body(input[_B], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Body.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_MessageDsn = (input, context) => {
    const entries = {};
    if (input[_RM] != null) {
        entries[_RM] = input[_RM];
    }
    if (input[_AD] != null) {
        entries[_AD] = __serializeDateTime(input[_AD]);
    }
    if (input[_EF] != null) {
        const memberEntries = se_ExtensionFieldList(input[_EF], context);
        if (input[_EF]?.length === 0) {
            entries.ExtensionFields = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ExtensionFields.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_MessageTag = (input, context) => {
    const entries = {};
    if (input[_N] != null) {
        entries[_N] = input[_N];
    }
    if (input[_Va] != null) {
        entries[_Va] = input[_Va];
    }
    return entries;
};
const se_MessageTagList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        const memberEntries = se_MessageTag(entry, context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            entries[`member.${counter}.${key}`] = value;
        });
        counter++;
    }
    return entries;
};
const se_PolicyNameList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        entries[`member.${counter}`] = entry;
        counter++;
    }
    return entries;
};
const se_PutConfigurationSetDeliveryOptionsRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_DO] != null) {
        const memberEntries = se_DeliveryOptions(input[_DO], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `DeliveryOptions.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_PutIdentityPolicyRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_PN] != null) {
        entries[_PN] = input[_PN];
    }
    if (input[_P] != null) {
        entries[_P] = input[_P];
    }
    return entries;
};
const se_RawMessage = (input, context) => {
    const entries = {};
    if (input[_Da] != null) {
        entries[_Da] = context.base64Encoder(input[_Da]);
    }
    return entries;
};
const se_ReceiptAction = (input, context) => {
    const entries = {};
    if (input[_SA] != null) {
        const memberEntries = se_S3Action(input[_SA], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `S3Action.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_BAo] != null) {
        const memberEntries = se_BounceAction(input[_BAo], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `BounceAction.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_WA] != null) {
        const memberEntries = se_WorkmailAction(input[_WA], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `WorkmailAction.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_LA] != null) {
        const memberEntries = se_LambdaAction(input[_LA], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `LambdaAction.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_SAt] != null) {
        const memberEntries = se_StopAction(input[_SAt], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `StopAction.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_AHA] != null) {
        const memberEntries = se_AddHeaderAction(input[_AHA], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `AddHeaderAction.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_SNSA] != null) {
        const memberEntries = se_SNSAction(input[_SNSA], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `SNSAction.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_CAo] != null) {
        const memberEntries = se_ConnectAction(input[_CAo], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ConnectAction.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_ReceiptActionsList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        const memberEntries = se_ReceiptAction(entry, context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            entries[`member.${counter}.${key}`] = value;
        });
        counter++;
    }
    return entries;
};
const se_ReceiptFilter = (input, context) => {
    const entries = {};
    if (input[_N] != null) {
        entries[_N] = input[_N];
    }
    if (input[_IF] != null) {
        const memberEntries = se_ReceiptIpFilter(input[_IF], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `IpFilter.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_ReceiptIpFilter = (input, context) => {
    const entries = {};
    if (input[_P] != null) {
        entries[_P] = input[_P];
    }
    if (input[_Ci] != null) {
        entries[_Ci] = input[_Ci];
    }
    return entries;
};
const se_ReceiptRule = (input, context) => {
    const entries = {};
    if (input[_N] != null) {
        entries[_N] = input[_N];
    }
    if (input[_E] != null) {
        entries[_E] = input[_E];
    }
    if (input[_TP] != null) {
        entries[_TP] = input[_TP];
    }
    if (input[_Re] != null) {
        const memberEntries = se_RecipientsList(input[_Re], context);
        if (input[_Re]?.length === 0) {
            entries.Recipients = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Recipients.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_Ac] != null) {
        const memberEntries = se_ReceiptActionsList(input[_Ac], context);
        if (input[_Ac]?.length === 0) {
            entries.Actions = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Actions.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_SEc] != null) {
        entries[_SEc] = input[_SEc];
    }
    return entries;
};
const se_ReceiptRuleNamesList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        entries[`member.${counter}`] = entry;
        counter++;
    }
    return entries;
};
const se_RecipientDsnFields = (input, context) => {
    const entries = {};
    if (input[_FR] != null) {
        entries[_FR] = input[_FR];
    }
    if (input[_A] != null) {
        entries[_A] = input[_A];
    }
    if (input[_RMe] != null) {
        entries[_RMe] = input[_RMe];
    }
    if (input[_St] != null) {
        entries[_St] = input[_St];
    }
    if (input[_DCi] != null) {
        entries[_DCi] = input[_DCi];
    }
    if (input[_LAD] != null) {
        entries[_LAD] = __serializeDateTime(input[_LAD]);
    }
    if (input[_EF] != null) {
        const memberEntries = se_ExtensionFieldList(input[_EF], context);
        if (input[_EF]?.length === 0) {
            entries.ExtensionFields = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ExtensionFields.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_RecipientsList = (input, context) => {
    const entries = {};
    let counter = 1;
    for (const entry of input) {
        if (entry === null) {
            continue;
        }
        entries[`member.${counter}`] = entry;
        counter++;
    }
    return entries;
};
const se_ReorderReceiptRuleSetRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    if (input[_RNu] != null) {
        const memberEntries = se_ReceiptRuleNamesList(input[_RNu], context);
        if (input[_RNu]?.length === 0) {
            entries.RuleNames = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `RuleNames.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_S3Action = (input, context) => {
    const entries = {};
    if (input[_TA] != null) {
        entries[_TA] = input[_TA];
    }
    if (input[_BN] != null) {
        entries[_BN] = input[_BN];
    }
    if (input[_OKP] != null) {
        entries[_OKP] = input[_OKP];
    }
    if (input[_KKA] != null) {
        entries[_KKA] = input[_KKA];
    }
    if (input[_IRA] != null) {
        entries[_IRA] = input[_IRA];
    }
    return entries;
};
const se_SendBounceRequest = (input, context) => {
    const entries = {};
    if (input[_OMI] != null) {
        entries[_OMI] = input[_OMI];
    }
    if (input[_BS] != null) {
        entries[_BS] = input[_BS];
    }
    if (input[_Ex] != null) {
        entries[_Ex] = input[_Ex];
    }
    if (input[_MD] != null) {
        const memberEntries = se_MessageDsn(input[_MD], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `MessageDsn.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_BRIL] != null) {
        const memberEntries = se_BouncedRecipientInfoList(input[_BRIL], context);
        if (input[_BRIL]?.length === 0) {
            entries.BouncedRecipientInfoList = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `BouncedRecipientInfoList.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_BSA] != null) {
        entries[_BSA] = input[_BSA];
    }
    return entries;
};
const se_SendBulkTemplatedEmailRequest = (input, context) => {
    const entries = {};
    if (input[_So] != null) {
        entries[_So] = input[_So];
    }
    if (input[_SAo] != null) {
        entries[_SAo] = input[_SAo];
    }
    if (input[_RTA] != null) {
        const memberEntries = se_AddressList(input[_RTA], context);
        if (input[_RTA]?.length === 0) {
            entries.ReplyToAddresses = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ReplyToAddresses.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RP] != null) {
        entries[_RP] = input[_RP];
    }
    if (input[_RPA] != null) {
        entries[_RPA] = input[_RPA];
    }
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_DTe] != null) {
        const memberEntries = se_MessageTagList(input[_DTe], context);
        if (input[_DTe]?.length === 0) {
            entries.DefaultTags = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `DefaultTags.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_Te] != null) {
        entries[_Te] = input[_Te];
    }
    if (input[_TAe] != null) {
        entries[_TAe] = input[_TAe];
    }
    if (input[_DTD] != null) {
        entries[_DTD] = input[_DTD];
    }
    if (input[_De] != null) {
        const memberEntries = se_BulkEmailDestinationList(input[_De], context);
        if (input[_De]?.length === 0) {
            entries.Destinations = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Destinations.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_SendCustomVerificationEmailRequest = (input, context) => {
    const entries = {};
    if (input[_EA] != null) {
        entries[_EA] = input[_EA];
    }
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    return entries;
};
const se_SendEmailRequest = (input, context) => {
    const entries = {};
    if (input[_So] != null) {
        entries[_So] = input[_So];
    }
    if (input[_D] != null) {
        const memberEntries = se_Destination(input[_D], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Destination.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_M] != null) {
        const memberEntries = se_Message(input[_M], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Message.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RTA] != null) {
        const memberEntries = se_AddressList(input[_RTA], context);
        if (input[_RTA]?.length === 0) {
            entries.ReplyToAddresses = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ReplyToAddresses.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RP] != null) {
        entries[_RP] = input[_RP];
    }
    if (input[_SAo] != null) {
        entries[_SAo] = input[_SAo];
    }
    if (input[_RPA] != null) {
        entries[_RPA] = input[_RPA];
    }
    if (input[_Ta] != null) {
        const memberEntries = se_MessageTagList(input[_Ta], context);
        if (input[_Ta]?.length === 0) {
            entries.Tags = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Tags.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    return entries;
};
const se_SendRawEmailRequest = (input, context) => {
    const entries = {};
    if (input[_So] != null) {
        entries[_So] = input[_So];
    }
    if (input[_De] != null) {
        const memberEntries = se_AddressList(input[_De], context);
        if (input[_De]?.length === 0) {
            entries.Destinations = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Destinations.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RMa] != null) {
        const memberEntries = se_RawMessage(input[_RMa], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `RawMessage.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_FAr] != null) {
        entries[_FAr] = input[_FAr];
    }
    if (input[_SAo] != null) {
        entries[_SAo] = input[_SAo];
    }
    if (input[_RPA] != null) {
        entries[_RPA] = input[_RPA];
    }
    if (input[_Ta] != null) {
        const memberEntries = se_MessageTagList(input[_Ta], context);
        if (input[_Ta]?.length === 0) {
            entries.Tags = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Tags.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    return entries;
};
const se_SendTemplatedEmailRequest = (input, context) => {
    const entries = {};
    if (input[_So] != null) {
        entries[_So] = input[_So];
    }
    if (input[_D] != null) {
        const memberEntries = se_Destination(input[_D], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Destination.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RTA] != null) {
        const memberEntries = se_AddressList(input[_RTA], context);
        if (input[_RTA]?.length === 0) {
            entries.ReplyToAddresses = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `ReplyToAddresses.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_RP] != null) {
        entries[_RP] = input[_RP];
    }
    if (input[_SAo] != null) {
        entries[_SAo] = input[_SAo];
    }
    if (input[_RPA] != null) {
        entries[_RPA] = input[_RPA];
    }
    if (input[_Ta] != null) {
        const memberEntries = se_MessageTagList(input[_Ta], context);
        if (input[_Ta]?.length === 0) {
            entries.Tags = [];
        }
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Tags.${key}`;
            entries[loc] = value;
        });
    }
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_Te] != null) {
        entries[_Te] = input[_Te];
    }
    if (input[_TAe] != null) {
        entries[_TAe] = input[_TAe];
    }
    if (input[_TD] != null) {
        entries[_TD] = input[_TD];
    }
    return entries;
};
const se_SetActiveReceiptRuleSetRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    return entries;
};
const se_SetIdentityDkimEnabledRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_DE] != null) {
        entries[_DE] = input[_DE];
    }
    return entries;
};
const se_SetIdentityFeedbackForwardingEnabledRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_FE] != null) {
        entries[_FE] = input[_FE];
    }
    return entries;
};
const se_SetIdentityHeadersInNotificationsEnabledRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_NTo] != null) {
        entries[_NTo] = input[_NTo];
    }
    if (input[_E] != null) {
        entries[_E] = input[_E];
    }
    return entries;
};
const se_SetIdentityMailFromDomainRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_MFD] != null) {
        entries[_MFD] = input[_MFD];
    }
    if (input[_BOMXF] != null) {
        entries[_BOMXF] = input[_BOMXF];
    }
    return entries;
};
const se_SetIdentityNotificationTopicRequest = (input, context) => {
    const entries = {};
    if (input[_I] != null) {
        entries[_I] = input[_I];
    }
    if (input[_NTo] != null) {
        entries[_NTo] = input[_NTo];
    }
    if (input[_ST] != null) {
        entries[_ST] = input[_ST];
    }
    return entries;
};
const se_SetReceiptRulePositionRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    if (input[_RN] != null) {
        entries[_RN] = input[_RN];
    }
    if (input[_Af] != null) {
        entries[_Af] = input[_Af];
    }
    return entries;
};
const se_SNSAction = (input, context) => {
    const entries = {};
    if (input[_TA] != null) {
        entries[_TA] = input[_TA];
    }
    if (input[_En] != null) {
        entries[_En] = input[_En];
    }
    return entries;
};
const se_SNSDestination = (input, context) => {
    const entries = {};
    if (input[_TARN] != null) {
        entries[_TARN] = input[_TARN];
    }
    return entries;
};
const se_StopAction = (input, context) => {
    const entries = {};
    if (input[_Sc] != null) {
        entries[_Sc] = input[_Sc];
    }
    if (input[_TA] != null) {
        entries[_TA] = input[_TA];
    }
    return entries;
};
const se_Template = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    if (input[_SP] != null) {
        entries[_SP] = input[_SP];
    }
    if (input[_TPe] != null) {
        entries[_TPe] = input[_TPe];
    }
    if (input[_HP] != null) {
        entries[_HP] = input[_HP];
    }
    return entries;
};
const se_TestRenderTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    if (input[_TD] != null) {
        entries[_TD] = input[_TD];
    }
    return entries;
};
const se_TrackingOptions = (input, context) => {
    const entries = {};
    if (input[_CRD] != null) {
        entries[_CRD] = input[_CRD];
    }
    return entries;
};
const se_UpdateAccountSendingEnabledRequest = (input, context) => {
    const entries = {};
    if (input[_E] != null) {
        entries[_E] = input[_E];
    }
    return entries;
};
const se_UpdateConfigurationSetEventDestinationRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_ED] != null) {
        const memberEntries = se_EventDestination(input[_ED], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `EventDestination.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_UpdateConfigurationSetReputationMetricsEnabledRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_E] != null) {
        entries[_E] = input[_E];
    }
    return entries;
};
const se_UpdateConfigurationSetSendingEnabledRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_E] != null) {
        entries[_E] = input[_E];
    }
    return entries;
};
const se_UpdateConfigurationSetTrackingOptionsRequest = (input, context) => {
    const entries = {};
    if (input[_CSN] != null) {
        entries[_CSN] = input[_CSN];
    }
    if (input[_TO] != null) {
        const memberEntries = se_TrackingOptions(input[_TO], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `TrackingOptions.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_UpdateCustomVerificationEmailTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_TN] != null) {
        entries[_TN] = input[_TN];
    }
    if (input[_FEA] != null) {
        entries[_FEA] = input[_FEA];
    }
    if (input[_TS] != null) {
        entries[_TS] = input[_TS];
    }
    if (input[_TC] != null) {
        entries[_TC] = input[_TC];
    }
    if (input[_SRURL] != null) {
        entries[_SRURL] = input[_SRURL];
    }
    if (input[_FRURL] != null) {
        entries[_FRURL] = input[_FRURL];
    }
    return entries;
};
const se_UpdateReceiptRuleRequest = (input, context) => {
    const entries = {};
    if (input[_RSN] != null) {
        entries[_RSN] = input[_RSN];
    }
    if (input[_Ru] != null) {
        const memberEntries = se_ReceiptRule(input[_Ru], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Rule.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_UpdateTemplateRequest = (input, context) => {
    const entries = {};
    if (input[_Te] != null) {
        const memberEntries = se_Template(input[_Te], context);
        Object.entries(memberEntries).forEach(([key, value]) => {
            const loc = `Template.${key}`;
            entries[loc] = value;
        });
    }
    return entries;
};
const se_VerifyDomainDkimRequest = (input, context) => {
    const entries = {};
    if (input[_Do] != null) {
        entries[_Do] = input[_Do];
    }
    return entries;
};
const se_VerifyDomainIdentityRequest = (input, context) => {
    const entries = {};
    if (input[_Do] != null) {
        entries[_Do] = input[_Do];
    }
    return entries;
};
const se_VerifyEmailAddressRequest = (input, context) => {
    const entries = {};
    if (input[_EA] != null) {
        entries[_EA] = input[_EA];
    }
    return entries;
};
const se_VerifyEmailIdentityRequest = (input, context) => {
    const entries = {};
    if (input[_EA] != null) {
        entries[_EA] = input[_EA];
    }
    return entries;
};
const se_WorkmailAction = (input, context) => {
    const entries = {};
    if (input[_TA] != null) {
        entries[_TA] = input[_TA];
    }
    if (input[_OA] != null) {
        entries[_OA] = input[_OA];
    }
    return entries;
};
const de_AccountSendingPausedException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_AddHeaderAction = (output, context) => {
    const contents = {};
    if (output[_HN] != null) {
        contents[_HN] = __expectString(output[_HN]);
    }
    if (output[_HV] != null) {
        contents[_HV] = __expectString(output[_HV]);
    }
    return contents;
};
const de_AddressList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return __expectString(entry);
    });
};
const de_AlreadyExistsException = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_BounceAction = (output, context) => {
    const contents = {};
    if (output[_TA] != null) {
        contents[_TA] = __expectString(output[_TA]);
    }
    if (output[_SRC] != null) {
        contents[_SRC] = __expectString(output[_SRC]);
    }
    if (output[_SC] != null) {
        contents[_SC] = __expectString(output[_SC]);
    }
    if (output[_M] != null) {
        contents[_M] = __expectString(output[_M]);
    }
    if (output[_S] != null) {
        contents[_S] = __expectString(output[_S]);
    }
    return contents;
};
const de_BulkEmailDestinationStatus = (output, context) => {
    const contents = {};
    if (output[_St] != null) {
        contents[_St] = __expectString(output[_St]);
    }
    if (output[_Er] != null) {
        contents[_Er] = __expectString(output[_Er]);
    }
    if (output[_MIe] != null) {
        contents[_MIe] = __expectString(output[_MIe]);
    }
    return contents;
};
const de_BulkEmailDestinationStatusList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_BulkEmailDestinationStatus(entry, context);
    });
};
const de_CannotDeleteException = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_CloneReceiptRuleSetResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CloudWatchDestination = (output, context) => {
    const contents = {};
    if (String(output.DimensionConfigurations).trim() === "") {
        contents[_DC] = [];
    }
    else if (output[_DC] != null && output[_DC][_me] != null) {
        contents[_DC] = de_CloudWatchDimensionConfigurations(__getArrayIfSingleItem(output[_DC][_me]), context);
    }
    return contents;
};
const de_CloudWatchDimensionConfiguration = (output, context) => {
    const contents = {};
    if (output[_DN] != null) {
        contents[_DN] = __expectString(output[_DN]);
    }
    if (output[_DVS] != null) {
        contents[_DVS] = __expectString(output[_DVS]);
    }
    if (output[_DDV] != null) {
        contents[_DDV] = __expectString(output[_DDV]);
    }
    return contents;
};
const de_CloudWatchDimensionConfigurations = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_CloudWatchDimensionConfiguration(entry, context);
    });
};
const de_ConfigurationSet = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    return contents;
};
const de_ConfigurationSetAlreadyExistsException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_ConfigurationSetDoesNotExistException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_ConfigurationSets = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_ConfigurationSet(entry, context);
    });
};
const de_ConfigurationSetSendingPausedException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_ConnectAction = (output, context) => {
    const contents = {};
    if (output[_IARN] != null) {
        contents[_IARN] = __expectString(output[_IARN]);
    }
    if (output[_IAMRARN] != null) {
        contents[_IAMRARN] = __expectString(output[_IAMRARN]);
    }
    return contents;
};
const de_CreateConfigurationSetEventDestinationResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CreateConfigurationSetResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CreateConfigurationSetTrackingOptionsResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CreateReceiptFilterResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CreateReceiptRuleResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CreateReceiptRuleSetResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CreateTemplateResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_CustomVerificationEmailInvalidContentException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_CustomVerificationEmailTemplate = (output, context) => {
    const contents = {};
    if (output[_TN] != null) {
        contents[_TN] = __expectString(output[_TN]);
    }
    if (output[_FEA] != null) {
        contents[_FEA] = __expectString(output[_FEA]);
    }
    if (output[_TS] != null) {
        contents[_TS] = __expectString(output[_TS]);
    }
    if (output[_SRURL] != null) {
        contents[_SRURL] = __expectString(output[_SRURL]);
    }
    if (output[_FRURL] != null) {
        contents[_FRURL] = __expectString(output[_FRURL]);
    }
    return contents;
};
const de_CustomVerificationEmailTemplateAlreadyExistsException = (output, context) => {
    const contents = {};
    if (output[_CVETN] != null) {
        contents[_CVETN] = __expectString(output[_CVETN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_CustomVerificationEmailTemplateDoesNotExistException = (output, context) => {
    const contents = {};
    if (output[_CVETN] != null) {
        contents[_CVETN] = __expectString(output[_CVETN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_CustomVerificationEmailTemplates = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_CustomVerificationEmailTemplate(entry, context);
    });
};
const de_DeleteConfigurationSetEventDestinationResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteConfigurationSetResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteConfigurationSetTrackingOptionsResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteIdentityPolicyResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteIdentityResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteReceiptFilterResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteReceiptRuleResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteReceiptRuleSetResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeleteTemplateResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_DeliveryOptions = (output, context) => {
    const contents = {};
    if (output[_TP] != null) {
        contents[_TP] = __expectString(output[_TP]);
    }
    return contents;
};
const de_DescribeActiveReceiptRuleSetResponse = (output, context) => {
    const contents = {};
    if (output[_Me] != null) {
        contents[_Me] = de_ReceiptRuleSetMetadata(output[_Me], context);
    }
    if (String(output.Rules).trim() === "") {
        contents[_Rul] = [];
    }
    else if (output[_Rul] != null && output[_Rul][_me] != null) {
        contents[_Rul] = de_ReceiptRulesList(__getArrayIfSingleItem(output[_Rul][_me]), context);
    }
    return contents;
};
const de_DescribeConfigurationSetResponse = (output, context) => {
    const contents = {};
    if (output[_CS] != null) {
        contents[_CS] = de_ConfigurationSet(output[_CS], context);
    }
    if (String(output.EventDestinations).trim() === "") {
        contents[_EDv] = [];
    }
    else if (output[_EDv] != null && output[_EDv][_me] != null) {
        contents[_EDv] = de_EventDestinations(__getArrayIfSingleItem(output[_EDv][_me]), context);
    }
    if (output[_TO] != null) {
        contents[_TO] = de_TrackingOptions(output[_TO], context);
    }
    if (output[_DO] != null) {
        contents[_DO] = de_DeliveryOptions(output[_DO], context);
    }
    if (output[_RO] != null) {
        contents[_RO] = de_ReputationOptions(output[_RO], context);
    }
    return contents;
};
const de_DescribeReceiptRuleResponse = (output, context) => {
    const contents = {};
    if (output[_Ru] != null) {
        contents[_Ru] = de_ReceiptRule(output[_Ru], context);
    }
    return contents;
};
const de_DescribeReceiptRuleSetResponse = (output, context) => {
    const contents = {};
    if (output[_Me] != null) {
        contents[_Me] = de_ReceiptRuleSetMetadata(output[_Me], context);
    }
    if (String(output.Rules).trim() === "") {
        contents[_Rul] = [];
    }
    else if (output[_Rul] != null && output[_Rul][_me] != null) {
        contents[_Rul] = de_ReceiptRulesList(__getArrayIfSingleItem(output[_Rul][_me]), context);
    }
    return contents;
};
const de_DkimAttributes = (output, context) => {
    return output.reduce((acc, pair) => {
        if (pair["value"] === null) {
            return acc;
        }
        acc[pair["key"]] = de_IdentityDkimAttributes(pair["value"], context);
        return acc;
    }, {});
};
const de_EventDestination = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_E] != null) {
        contents[_E] = __parseBoolean(output[_E]);
    }
    if (String(output.MatchingEventTypes).trim() === "") {
        contents[_MET] = [];
    }
    else if (output[_MET] != null && output[_MET][_me] != null) {
        contents[_MET] = de_EventTypes(__getArrayIfSingleItem(output[_MET][_me]), context);
    }
    if (output[_KFD] != null) {
        contents[_KFD] = de_KinesisFirehoseDestination(output[_KFD], context);
    }
    if (output[_CWD] != null) {
        contents[_CWD] = de_CloudWatchDestination(output[_CWD], context);
    }
    if (output[_SNSD] != null) {
        contents[_SNSD] = de_SNSDestination(output[_SNSD], context);
    }
    return contents;
};
const de_EventDestinationAlreadyExistsException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_EDN] != null) {
        contents[_EDN] = __expectString(output[_EDN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_EventDestinationDoesNotExistException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_EDN] != null) {
        contents[_EDN] = __expectString(output[_EDN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_EventDestinations = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_EventDestination(entry, context);
    });
};
const de_EventTypes = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return __expectString(entry);
    });
};
const de_FromEmailAddressNotVerifiedException = (output, context) => {
    const contents = {};
    if (output[_FEA] != null) {
        contents[_FEA] = __expectString(output[_FEA]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_GetAccountSendingEnabledResponse = (output, context) => {
    const contents = {};
    if (output[_E] != null) {
        contents[_E] = __parseBoolean(output[_E]);
    }
    return contents;
};
const de_GetCustomVerificationEmailTemplateResponse = (output, context) => {
    const contents = {};
    if (output[_TN] != null) {
        contents[_TN] = __expectString(output[_TN]);
    }
    if (output[_FEA] != null) {
        contents[_FEA] = __expectString(output[_FEA]);
    }
    if (output[_TS] != null) {
        contents[_TS] = __expectString(output[_TS]);
    }
    if (output[_TC] != null) {
        contents[_TC] = __expectString(output[_TC]);
    }
    if (output[_SRURL] != null) {
        contents[_SRURL] = __expectString(output[_SRURL]);
    }
    if (output[_FRURL] != null) {
        contents[_FRURL] = __expectString(output[_FRURL]);
    }
    return contents;
};
const de_GetIdentityDkimAttributesResponse = (output, context) => {
    const contents = {};
    if (String(output.DkimAttributes).trim() === "") {
        contents[_DA] = {};
    }
    else if (output[_DA] != null && output[_DA][_e] != null) {
        contents[_DA] = de_DkimAttributes(__getArrayIfSingleItem(output[_DA][_e]), context);
    }
    return contents;
};
const de_GetIdentityMailFromDomainAttributesResponse = (output, context) => {
    const contents = {};
    if (String(output.MailFromDomainAttributes).trim() === "") {
        contents[_MFDA] = {};
    }
    else if (output[_MFDA] != null && output[_MFDA][_e] != null) {
        contents[_MFDA] = de_MailFromDomainAttributes(__getArrayIfSingleItem(output[_MFDA][_e]), context);
    }
    return contents;
};
const de_GetIdentityNotificationAttributesResponse = (output, context) => {
    const contents = {};
    if (String(output.NotificationAttributes).trim() === "") {
        contents[_NA] = {};
    }
    else if (output[_NA] != null && output[_NA][_e] != null) {
        contents[_NA] = de_NotificationAttributes(__getArrayIfSingleItem(output[_NA][_e]), context);
    }
    return contents;
};
const de_GetIdentityPoliciesResponse = (output, context) => {
    const contents = {};
    if (String(output.Policies).trim() === "") {
        contents[_Po] = {};
    }
    else if (output[_Po] != null && output[_Po][_e] != null) {
        contents[_Po] = de_PolicyMap(__getArrayIfSingleItem(output[_Po][_e]), context);
    }
    return contents;
};
const de_GetIdentityVerificationAttributesResponse = (output, context) => {
    const contents = {};
    if (String(output.VerificationAttributes).trim() === "") {
        contents[_VA] = {};
    }
    else if (output[_VA] != null && output[_VA][_e] != null) {
        contents[_VA] = de_VerificationAttributes(__getArrayIfSingleItem(output[_VA][_e]), context);
    }
    return contents;
};
const de_GetSendQuotaResponse = (output, context) => {
    const contents = {};
    if (output[_MHS] != null) {
        contents[_MHS] = __strictParseFloat(output[_MHS]);
    }
    if (output[_MSR] != null) {
        contents[_MSR] = __strictParseFloat(output[_MSR]);
    }
    if (output[_SLH] != null) {
        contents[_SLH] = __strictParseFloat(output[_SLH]);
    }
    return contents;
};
const de_GetSendStatisticsResponse = (output, context) => {
    const contents = {};
    if (String(output.SendDataPoints).trim() === "") {
        contents[_SDP] = [];
    }
    else if (output[_SDP] != null && output[_SDP][_me] != null) {
        contents[_SDP] = de_SendDataPointList(__getArrayIfSingleItem(output[_SDP][_me]), context);
    }
    return contents;
};
const de_GetTemplateResponse = (output, context) => {
    const contents = {};
    if (output[_Te] != null) {
        contents[_Te] = de_Template(output[_Te], context);
    }
    return contents;
};
const de_IdentityDkimAttributes = (output, context) => {
    const contents = {};
    if (output[_DE] != null) {
        contents[_DE] = __parseBoolean(output[_DE]);
    }
    if (output[_DVSk] != null) {
        contents[_DVSk] = __expectString(output[_DVSk]);
    }
    if (String(output.DkimTokens).trim() === "") {
        contents[_DTk] = [];
    }
    else if (output[_DTk] != null && output[_DTk][_me] != null) {
        contents[_DTk] = de_VerificationTokenList(__getArrayIfSingleItem(output[_DTk][_me]), context);
    }
    return contents;
};
const de_IdentityList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return __expectString(entry);
    });
};
const de_IdentityMailFromDomainAttributes = (output, context) => {
    const contents = {};
    if (output[_MFD] != null) {
        contents[_MFD] = __expectString(output[_MFD]);
    }
    if (output[_MFDS] != null) {
        contents[_MFDS] = __expectString(output[_MFDS]);
    }
    if (output[_BOMXF] != null) {
        contents[_BOMXF] = __expectString(output[_BOMXF]);
    }
    return contents;
};
const de_IdentityNotificationAttributes = (output, context) => {
    const contents = {};
    if (output[_BTo] != null) {
        contents[_BTo] = __expectString(output[_BTo]);
    }
    if (output[_CTo] != null) {
        contents[_CTo] = __expectString(output[_CTo]);
    }
    if (output[_DTel] != null) {
        contents[_DTel] = __expectString(output[_DTel]);
    }
    if (output[_FE] != null) {
        contents[_FE] = __parseBoolean(output[_FE]);
    }
    if (output[_HIBNE] != null) {
        contents[_HIBNE] = __parseBoolean(output[_HIBNE]);
    }
    if (output[_HICNE] != null) {
        contents[_HICNE] = __parseBoolean(output[_HICNE]);
    }
    if (output[_HIDNE] != null) {
        contents[_HIDNE] = __parseBoolean(output[_HIDNE]);
    }
    return contents;
};
const de_IdentityVerificationAttributes = (output, context) => {
    const contents = {};
    if (output[_VS] != null) {
        contents[_VS] = __expectString(output[_VS]);
    }
    if (output[_VT] != null) {
        contents[_VT] = __expectString(output[_VT]);
    }
    return contents;
};
const de_InvalidCloudWatchDestinationException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_EDN] != null) {
        contents[_EDN] = __expectString(output[_EDN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidConfigurationSetException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidDeliveryOptionsException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidFirehoseDestinationException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_EDN] != null) {
        contents[_EDN] = __expectString(output[_EDN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidLambdaFunctionException = (output, context) => {
    const contents = {};
    if (output[_FA] != null) {
        contents[_FA] = __expectString(output[_FA]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidPolicyException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidRenderingParameterException = (output, context) => {
    const contents = {};
    if (output[_TN] != null) {
        contents[_TN] = __expectString(output[_TN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidS3ConfigurationException = (output, context) => {
    const contents = {};
    if (output[_Bu] != null) {
        contents[_Bu] = __expectString(output[_Bu]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidSNSDestinationException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_EDN] != null) {
        contents[_EDN] = __expectString(output[_EDN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidSnsTopicException = (output, context) => {
    const contents = {};
    if (output[_To] != null) {
        contents[_To] = __expectString(output[_To]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidTemplateException = (output, context) => {
    const contents = {};
    if (output[_TN] != null) {
        contents[_TN] = __expectString(output[_TN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_InvalidTrackingOptionsException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_KinesisFirehoseDestination = (output, context) => {
    const contents = {};
    if (output[_IAMRARN] != null) {
        contents[_IAMRARN] = __expectString(output[_IAMRARN]);
    }
    if (output[_DSARN] != null) {
        contents[_DSARN] = __expectString(output[_DSARN]);
    }
    return contents;
};
const de_LambdaAction = (output, context) => {
    const contents = {};
    if (output[_TA] != null) {
        contents[_TA] = __expectString(output[_TA]);
    }
    if (output[_FA] != null) {
        contents[_FA] = __expectString(output[_FA]);
    }
    if (output[_IT] != null) {
        contents[_IT] = __expectString(output[_IT]);
    }
    return contents;
};
const de_LimitExceededException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_ListConfigurationSetsResponse = (output, context) => {
    const contents = {};
    if (String(output.ConfigurationSets).trim() === "") {
        contents[_CSo] = [];
    }
    else if (output[_CSo] != null && output[_CSo][_me] != null) {
        contents[_CSo] = de_ConfigurationSets(__getArrayIfSingleItem(output[_CSo][_me]), context);
    }
    if (output[_NT] != null) {
        contents[_NT] = __expectString(output[_NT]);
    }
    return contents;
};
const de_ListCustomVerificationEmailTemplatesResponse = (output, context) => {
    const contents = {};
    if (String(output.CustomVerificationEmailTemplates).trim() === "") {
        contents[_CVET] = [];
    }
    else if (output[_CVET] != null && output[_CVET][_me] != null) {
        contents[_CVET] = de_CustomVerificationEmailTemplates(__getArrayIfSingleItem(output[_CVET][_me]), context);
    }
    if (output[_NT] != null) {
        contents[_NT] = __expectString(output[_NT]);
    }
    return contents;
};
const de_ListIdentitiesResponse = (output, context) => {
    const contents = {};
    if (String(output.Identities).trim() === "") {
        contents[_Id] = [];
    }
    else if (output[_Id] != null && output[_Id][_me] != null) {
        contents[_Id] = de_IdentityList(__getArrayIfSingleItem(output[_Id][_me]), context);
    }
    if (output[_NT] != null) {
        contents[_NT] = __expectString(output[_NT]);
    }
    return contents;
};
const de_ListIdentityPoliciesResponse = (output, context) => {
    const contents = {};
    if (String(output.PolicyNames).trim() === "") {
        contents[_PNo] = [];
    }
    else if (output[_PNo] != null && output[_PNo][_me] != null) {
        contents[_PNo] = de_PolicyNameList(__getArrayIfSingleItem(output[_PNo][_me]), context);
    }
    return contents;
};
const de_ListReceiptFiltersResponse = (output, context) => {
    const contents = {};
    if (String(output.Filters).trim() === "") {
        contents[_Fi] = [];
    }
    else if (output[_Fi] != null && output[_Fi][_me] != null) {
        contents[_Fi] = de_ReceiptFilterList(__getArrayIfSingleItem(output[_Fi][_me]), context);
    }
    return contents;
};
const de_ListReceiptRuleSetsResponse = (output, context) => {
    const contents = {};
    if (String(output.RuleSets).trim() === "") {
        contents[_RS] = [];
    }
    else if (output[_RS] != null && output[_RS][_me] != null) {
        contents[_RS] = de_ReceiptRuleSetsLists(__getArrayIfSingleItem(output[_RS][_me]), context);
    }
    if (output[_NT] != null) {
        contents[_NT] = __expectString(output[_NT]);
    }
    return contents;
};
const de_ListTemplatesResponse = (output, context) => {
    const contents = {};
    if (String(output.TemplatesMetadata).trim() === "") {
        contents[_TM] = [];
    }
    else if (output[_TM] != null && output[_TM][_me] != null) {
        contents[_TM] = de_TemplateMetadataList(__getArrayIfSingleItem(output[_TM][_me]), context);
    }
    if (output[_NT] != null) {
        contents[_NT] = __expectString(output[_NT]);
    }
    return contents;
};
const de_ListVerifiedEmailAddressesResponse = (output, context) => {
    const contents = {};
    if (String(output.VerifiedEmailAddresses).trim() === "") {
        contents[_VEAe] = [];
    }
    else if (output[_VEAe] != null && output[_VEAe][_me] != null) {
        contents[_VEAe] = de_AddressList(__getArrayIfSingleItem(output[_VEAe][_me]), context);
    }
    return contents;
};
const de_MailFromDomainAttributes = (output, context) => {
    return output.reduce((acc, pair) => {
        if (pair["value"] === null) {
            return acc;
        }
        acc[pair["key"]] = de_IdentityMailFromDomainAttributes(pair["value"], context);
        return acc;
    }, {});
};
const de_MailFromDomainNotVerifiedException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_MessageRejected = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_MissingRenderingAttributeException = (output, context) => {
    const contents = {};
    if (output[_TN] != null) {
        contents[_TN] = __expectString(output[_TN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_NotificationAttributes = (output, context) => {
    return output.reduce((acc, pair) => {
        if (pair["value"] === null) {
            return acc;
        }
        acc[pair["key"]] = de_IdentityNotificationAttributes(pair["value"], context);
        return acc;
    }, {});
};
const de_PolicyMap = (output, context) => {
    return output.reduce((acc, pair) => {
        if (pair["value"] === null) {
            return acc;
        }
        acc[pair["key"]] = __expectString(pair["value"]);
        return acc;
    }, {});
};
const de_PolicyNameList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return __expectString(entry);
    });
};
const de_ProductionAccessNotGrantedException = (output, context) => {
    const contents = {};
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_PutConfigurationSetDeliveryOptionsResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_PutIdentityPolicyResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_ReceiptAction = (output, context) => {
    const contents = {};
    if (output[_SA] != null) {
        contents[_SA] = de_S3Action(output[_SA], context);
    }
    if (output[_BAo] != null) {
        contents[_BAo] = de_BounceAction(output[_BAo], context);
    }
    if (output[_WA] != null) {
        contents[_WA] = de_WorkmailAction(output[_WA], context);
    }
    if (output[_LA] != null) {
        contents[_LA] = de_LambdaAction(output[_LA], context);
    }
    if (output[_SAt] != null) {
        contents[_SAt] = de_StopAction(output[_SAt], context);
    }
    if (output[_AHA] != null) {
        contents[_AHA] = de_AddHeaderAction(output[_AHA], context);
    }
    if (output[_SNSA] != null) {
        contents[_SNSA] = de_SNSAction(output[_SNSA], context);
    }
    if (output[_CAo] != null) {
        contents[_CAo] = de_ConnectAction(output[_CAo], context);
    }
    return contents;
};
const de_ReceiptActionsList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_ReceiptAction(entry, context);
    });
};
const de_ReceiptFilter = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_IF] != null) {
        contents[_IF] = de_ReceiptIpFilter(output[_IF], context);
    }
    return contents;
};
const de_ReceiptFilterList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_ReceiptFilter(entry, context);
    });
};
const de_ReceiptIpFilter = (output, context) => {
    const contents = {};
    if (output[_P] != null) {
        contents[_P] = __expectString(output[_P]);
    }
    if (output[_Ci] != null) {
        contents[_Ci] = __expectString(output[_Ci]);
    }
    return contents;
};
const de_ReceiptRule = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_E] != null) {
        contents[_E] = __parseBoolean(output[_E]);
    }
    if (output[_TP] != null) {
        contents[_TP] = __expectString(output[_TP]);
    }
    if (String(output.Recipients).trim() === "") {
        contents[_Re] = [];
    }
    else if (output[_Re] != null && output[_Re][_me] != null) {
        contents[_Re] = de_RecipientsList(__getArrayIfSingleItem(output[_Re][_me]), context);
    }
    if (String(output.Actions).trim() === "") {
        contents[_Ac] = [];
    }
    else if (output[_Ac] != null && output[_Ac][_me] != null) {
        contents[_Ac] = de_ReceiptActionsList(__getArrayIfSingleItem(output[_Ac][_me]), context);
    }
    if (output[_SEc] != null) {
        contents[_SEc] = __parseBoolean(output[_SEc]);
    }
    return contents;
};
const de_ReceiptRuleSetMetadata = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_CTr] != null) {
        contents[_CTr] = __expectNonNull(__parseRfc3339DateTimeWithOffset(output[_CTr]));
    }
    return contents;
};
const de_ReceiptRuleSetsLists = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_ReceiptRuleSetMetadata(entry, context);
    });
};
const de_ReceiptRulesList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_ReceiptRule(entry, context);
    });
};
const de_RecipientsList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return __expectString(entry);
    });
};
const de_ReorderReceiptRuleSetResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_ReputationOptions = (output, context) => {
    const contents = {};
    if (output[_SEe] != null) {
        contents[_SEe] = __parseBoolean(output[_SEe]);
    }
    if (output[_RME] != null) {
        contents[_RME] = __parseBoolean(output[_RME]);
    }
    if (output[_LFS] != null) {
        contents[_LFS] = __expectNonNull(__parseRfc3339DateTimeWithOffset(output[_LFS]));
    }
    return contents;
};
const de_RuleDoesNotExistException = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_RuleSetDoesNotExistException = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_S3Action = (output, context) => {
    const contents = {};
    if (output[_TA] != null) {
        contents[_TA] = __expectString(output[_TA]);
    }
    if (output[_BN] != null) {
        contents[_BN] = __expectString(output[_BN]);
    }
    if (output[_OKP] != null) {
        contents[_OKP] = __expectString(output[_OKP]);
    }
    if (output[_KKA] != null) {
        contents[_KKA] = __expectString(output[_KKA]);
    }
    if (output[_IRA] != null) {
        contents[_IRA] = __expectString(output[_IRA]);
    }
    return contents;
};
const de_SendBounceResponse = (output, context) => {
    const contents = {};
    if (output[_MIe] != null) {
        contents[_MIe] = __expectString(output[_MIe]);
    }
    return contents;
};
const de_SendBulkTemplatedEmailResponse = (output, context) => {
    const contents = {};
    if (String(output.Status).trim() === "") {
        contents[_St] = [];
    }
    else if (output[_St] != null && output[_St][_me] != null) {
        contents[_St] = de_BulkEmailDestinationStatusList(__getArrayIfSingleItem(output[_St][_me]), context);
    }
    return contents;
};
const de_SendCustomVerificationEmailResponse = (output, context) => {
    const contents = {};
    if (output[_MIe] != null) {
        contents[_MIe] = __expectString(output[_MIe]);
    }
    return contents;
};
const de_SendDataPoint = (output, context) => {
    const contents = {};
    if (output[_Ti] != null) {
        contents[_Ti] = __expectNonNull(__parseRfc3339DateTimeWithOffset(output[_Ti]));
    }
    if (output[_DAe] != null) {
        contents[_DAe] = __strictParseLong(output[_DAe]);
    }
    if (output[_Bo] != null) {
        contents[_Bo] = __strictParseLong(output[_Bo]);
    }
    if (output[_Co] != null) {
        contents[_Co] = __strictParseLong(output[_Co]);
    }
    if (output[_Rej] != null) {
        contents[_Rej] = __strictParseLong(output[_Rej]);
    }
    return contents;
};
const de_SendDataPointList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_SendDataPoint(entry, context);
    });
};
const de_SendEmailResponse = (output, context) => {
    const contents = {};
    if (output[_MIe] != null) {
        contents[_MIe] = __expectString(output[_MIe]);
    }
    return contents;
};
const de_SendRawEmailResponse = (output, context) => {
    const contents = {};
    if (output[_MIe] != null) {
        contents[_MIe] = __expectString(output[_MIe]);
    }
    return contents;
};
const de_SendTemplatedEmailResponse = (output, context) => {
    const contents = {};
    if (output[_MIe] != null) {
        contents[_MIe] = __expectString(output[_MIe]);
    }
    return contents;
};
const de_SetActiveReceiptRuleSetResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_SetIdentityDkimEnabledResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_SetIdentityFeedbackForwardingEnabledResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_SetIdentityHeadersInNotificationsEnabledResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_SetIdentityMailFromDomainResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_SetIdentityNotificationTopicResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_SetReceiptRulePositionResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_SNSAction = (output, context) => {
    const contents = {};
    if (output[_TA] != null) {
        contents[_TA] = __expectString(output[_TA]);
    }
    if (output[_En] != null) {
        contents[_En] = __expectString(output[_En]);
    }
    return contents;
};
const de_SNSDestination = (output, context) => {
    const contents = {};
    if (output[_TARN] != null) {
        contents[_TARN] = __expectString(output[_TARN]);
    }
    return contents;
};
const de_StopAction = (output, context) => {
    const contents = {};
    if (output[_Sc] != null) {
        contents[_Sc] = __expectString(output[_Sc]);
    }
    if (output[_TA] != null) {
        contents[_TA] = __expectString(output[_TA]);
    }
    return contents;
};
const de_Template = (output, context) => {
    const contents = {};
    if (output[_TN] != null) {
        contents[_TN] = __expectString(output[_TN]);
    }
    if (output[_SP] != null) {
        contents[_SP] = __expectString(output[_SP]);
    }
    if (output[_TPe] != null) {
        contents[_TPe] = __expectString(output[_TPe]);
    }
    if (output[_HP] != null) {
        contents[_HP] = __expectString(output[_HP]);
    }
    return contents;
};
const de_TemplateDoesNotExistException = (output, context) => {
    const contents = {};
    if (output[_TN] != null) {
        contents[_TN] = __expectString(output[_TN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_TemplateMetadata = (output, context) => {
    const contents = {};
    if (output[_N] != null) {
        contents[_N] = __expectString(output[_N]);
    }
    if (output[_CTr] != null) {
        contents[_CTr] = __expectNonNull(__parseRfc3339DateTimeWithOffset(output[_CTr]));
    }
    return contents;
};
const de_TemplateMetadataList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return de_TemplateMetadata(entry, context);
    });
};
const de_TestRenderTemplateResponse = (output, context) => {
    const contents = {};
    if (output[_RTe] != null) {
        contents[_RTe] = __expectString(output[_RTe]);
    }
    return contents;
};
const de_TrackingOptions = (output, context) => {
    const contents = {};
    if (output[_CRD] != null) {
        contents[_CRD] = __expectString(output[_CRD]);
    }
    return contents;
};
const de_TrackingOptionsAlreadyExistsException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_TrackingOptionsDoesNotExistException = (output, context) => {
    const contents = {};
    if (output[_CSN] != null) {
        contents[_CSN] = __expectString(output[_CSN]);
    }
    if (output[_m] != null) {
        contents[_m] = __expectString(output[_m]);
    }
    return contents;
};
const de_UpdateConfigurationSetEventDestinationResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_UpdateConfigurationSetTrackingOptionsResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_UpdateReceiptRuleResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_UpdateTemplateResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_VerificationAttributes = (output, context) => {
    return output.reduce((acc, pair) => {
        if (pair["value"] === null) {
            return acc;
        }
        acc[pair["key"]] = de_IdentityVerificationAttributes(pair["value"], context);
        return acc;
    }, {});
};
const de_VerificationTokenList = (output, context) => {
    return (output || [])
        .filter((e) => e != null)
        .map((entry) => {
        return __expectString(entry);
    });
};
const de_VerifyDomainDkimResponse = (output, context) => {
    const contents = {};
    if (String(output.DkimTokens).trim() === "") {
        contents[_DTk] = [];
    }
    else if (output[_DTk] != null && output[_DTk][_me] != null) {
        contents[_DTk] = de_VerificationTokenList(__getArrayIfSingleItem(output[_DTk][_me]), context);
    }
    return contents;
};
const de_VerifyDomainIdentityResponse = (output, context) => {
    const contents = {};
    if (output[_VT] != null) {
        contents[_VT] = __expectString(output[_VT]);
    }
    return contents;
};
const de_VerifyEmailIdentityResponse = (output, context) => {
    const contents = {};
    return contents;
};
const de_WorkmailAction = (output, context) => {
    const contents = {};
    if (output[_TA] != null) {
        contents[_TA] = __expectString(output[_TA]);
    }
    if (output[_OA] != null) {
        contents[_OA] = __expectString(output[_OA]);
    }
    return contents;
};
const deserializeMetadata = (output) => ({
    httpStatusCode: output.statusCode,
    requestId: output.headers["x-amzn-requestid"] ?? output.headers["x-amzn-request-id"] ?? output.headers["x-amz-request-id"],
    extendedRequestId: output.headers["x-amz-id-2"],
    cfId: output.headers["x-amz-cf-id"],
});
const collectBodyString = (streamBody, context) => collectBody(streamBody, context).then((body) => context.utf8Encoder(body));
const throwDefaultError = withBaseException(__BaseException);
const buildHttpRpcRequest = async (context, headers, path, resolvedHostname, body) => {
    const { hostname, protocol = "https", port, path: basePath } = await context.endpoint();
    const contents = {
        protocol,
        hostname,
        port,
        method: "POST",
        path: basePath.endsWith("/") ? basePath.slice(0, -1) + path : basePath + path,
        headers,
    };
    if (resolvedHostname !== undefined) {
        contents.hostname = resolvedHostname;
    }
    if (body !== undefined) {
        contents.body = body;
    }
    return new __HttpRequest(contents);
};
const SHARED_HEADERS = {
    "content-type": "application/x-www-form-urlencoded",
};
const _ = "2010-12-01";
const _A = "Action";
const _AD = "ArrivalDate";
const _AHA = "AddHeaderAction";
const _Ac = "Actions";
const _Af = "After";
const _B = "Body";
const _BA = "BccAddresses";
const _BAo = "BounceAction";
const _BN = "BucketName";
const _BOMXF = "BehaviorOnMXFailure";
const _BRIL = "BouncedRecipientInfoList";
const _BS = "BounceSender";
const _BSA = "BounceSenderArn";
const _BT = "BounceType";
const _BTo = "BounceTopic";
const _Bo = "Bounces";
const _Bu = "Bucket";
const _C = "Charset";
const _CA = "CcAddresses";
const _CAo = "ConnectAction";
const _CCS = "CreateConfigurationSet";
const _CCSED = "CreateConfigurationSetEventDestination";
const _CCSTO = "CreateConfigurationSetTrackingOptions";
const _CCVET = "CreateCustomVerificationEmailTemplate";
const _CRD = "CustomRedirectDomain";
const _CRF = "CreateReceiptFilter";
const _CRR = "CreateReceiptRule";
const _CRRS = "CloneReceiptRuleSet";
const _CRRSr = "CreateReceiptRuleSet";
const _CS = "ConfigurationSet";
const _CSAN = "ConfigurationSetAttributeNames";
const _CSN = "ConfigurationSetName";
const _CSo = "ConfigurationSets";
const _CT = "CreateTemplate";
const _CTo = "ComplaintTopic";
const _CTr = "CreatedTimestamp";
const _CVET = "CustomVerificationEmailTemplates";
const _CVETN = "CustomVerificationEmailTemplateName";
const _CWD = "CloudWatchDestination";
const _Ci = "Cidr";
const _Co = "Complaints";
const _D = "Destination";
const _DA = "DkimAttributes";
const _DARRS = "DescribeActiveReceiptRuleSet";
const _DAe = "DeliveryAttempts";
const _DC = "DimensionConfigurations";
const _DCS = "DeleteConfigurationSet";
const _DCSED = "DeleteConfigurationSetEventDestination";
const _DCSTO = "DeleteConfigurationSetTrackingOptions";
const _DCSe = "DescribeConfigurationSet";
const _DCVET = "DeleteCustomVerificationEmailTemplate";
const _DCi = "DiagnosticCode";
const _DDV = "DefaultDimensionValue";
const _DE = "DkimEnabled";
const _DI = "DeleteIdentity";
const _DIP = "DeleteIdentityPolicy";
const _DN = "DimensionName";
const _DO = "DeliveryOptions";
const _DRF = "DeleteReceiptFilter";
const _DRR = "DeleteReceiptRule";
const _DRRS = "DeleteReceiptRuleSet";
const _DRRSe = "DescribeReceiptRuleSet";
const _DRRe = "DescribeReceiptRule";
const _DSARN = "DeliveryStreamARN";
const _DT = "DeleteTemplate";
const _DTD = "DefaultTemplateData";
const _DTe = "DefaultTags";
const _DTel = "DeliveryTopic";
const _DTk = "DkimTokens";
const _DVEA = "DeleteVerifiedEmailAddress";
const _DVS = "DimensionValueSource";
const _DVSk = "DkimVerificationStatus";
const _Da = "Data";
const _De = "Destinations";
const _Do = "Domain";
const _E = "Enabled";
const _EA = "EmailAddress";
const _ED = "EventDestination";
const _EDN = "EventDestinationName";
const _EDv = "EventDestinations";
const _EF = "ExtensionFields";
const _En = "Encoding";
const _Er = "Error";
const _Ex = "Explanation";
const _F = "Filter";
const _FA = "FunctionArn";
const _FAr = "FromArn";
const _FE = "ForwardingEnabled";
const _FEA = "FromEmailAddress";
const _FN = "FilterName";
const _FR = "FinalRecipient";
const _FRURL = "FailureRedirectionURL";
const _Fi = "Filters";
const _GASE = "GetAccountSendingEnabled";
const _GCVET = "GetCustomVerificationEmailTemplate";
const _GIDA = "GetIdentityDkimAttributes";
const _GIMFDA = "GetIdentityMailFromDomainAttributes";
const _GINA = "GetIdentityNotificationAttributes";
const _GIP = "GetIdentityPolicies";
const _GIVA = "GetIdentityVerificationAttributes";
const _GSQ = "GetSendQuota";
const _GSS = "GetSendStatistics";
const _GT = "GetTemplate";
const _H = "Html";
const _HIBNE = "HeadersInBounceNotificationsEnabled";
const _HICNE = "HeadersInComplaintNotificationsEnabled";
const _HIDNE = "HeadersInDeliveryNotificationsEnabled";
const _HN = "HeaderName";
const _HP = "HtmlPart";
const _HV = "HeaderValue";
const _I = "Identity";
const _IAMRARN = "IAMRoleARN";
const _IARN = "InstanceARN";
const _IF = "IpFilter";
const _IRA = "IamRoleArn";
const _IT = "InvocationType";
const _ITd = "IdentityType";
const _Id = "Identities";
const _KFD = "KinesisFirehoseDestination";
const _KKA = "KmsKeyArn";
const _LA = "LambdaAction";
const _LAD = "LastAttemptDate";
const _LCS = "ListConfigurationSets";
const _LCVET = "ListCustomVerificationEmailTemplates";
const _LFS = "LastFreshStart";
const _LI = "ListIdentities";
const _LIP = "ListIdentityPolicies";
const _LRF = "ListReceiptFilters";
const _LRRS = "ListReceiptRuleSets";
const _LT = "ListTemplates";
const _LVEA = "ListVerifiedEmailAddresses";
const _M = "Message";
const _MD = "MessageDsn";
const _MET = "MatchingEventTypes";
const _MFD = "MailFromDomain";
const _MFDA = "MailFromDomainAttributes";
const _MFDS = "MailFromDomainStatus";
const _MHS = "Max24HourSend";
const _MI = "MaxItems";
const _MIe = "MessageId";
const _MR = "MaxResults";
const _MSR = "MaxSendRate";
const _Me = "Metadata";
const _N = "Name";
const _NA = "NotificationAttributes";
const _NT = "NextToken";
const _NTo = "NotificationType";
const _OA = "OrganizationArn";
const _OKP = "ObjectKeyPrefix";
const _OMI = "OriginalMessageId";
const _ORSN = "OriginalRuleSetName";
const _P = "Policy";
const _PCSDO = "PutConfigurationSetDeliveryOptions";
const _PIP = "PutIdentityPolicy";
const _PN = "PolicyName";
const _PNo = "PolicyNames";
const _Po = "Policies";
const _R = "Recipient";
const _RA = "RecipientArn";
const _RDF = "RecipientDsnFields";
const _RM = "ReportingMta";
const _RME = "ReputationMetricsEnabled";
const _RMa = "RawMessage";
const _RMe = "RemoteMta";
const _RN = "RuleName";
const _RNu = "RuleNames";
const _RO = "ReputationOptions";
const _RP = "ReturnPath";
const _RPA = "ReturnPathArn";
const _RRRS = "ReorderReceiptRuleSet";
const _RS = "RuleSets";
const _RSN = "RuleSetName";
const _RT = "ReplacementTags";
const _RTA = "ReplyToAddresses";
const _RTD = "ReplacementTemplateData";
const _RTe = "RenderedTemplate";
const _Re = "Recipients";
const _Rej = "Rejects";
const _Ru = "Rule";
const _Rul = "Rules";
const _S = "Sender";
const _SA = "S3Action";
const _SARRS = "SetActiveReceiptRuleSet";
const _SAo = "SourceArn";
const _SAt = "StopAction";
const _SB = "SendBounce";
const _SBTE = "SendBulkTemplatedEmail";
const _SC = "StatusCode";
const _SCVE = "SendCustomVerificationEmail";
const _SDP = "SendDataPoints";
const _SE = "SendEmail";
const _SEc = "ScanEnabled";
const _SEe = "SendingEnabled";
const _SIDE = "SetIdentityDkimEnabled";
const _SIFFE = "SetIdentityFeedbackForwardingEnabled";
const _SIHINE = "SetIdentityHeadersInNotificationsEnabled";
const _SIMFD = "SetIdentityMailFromDomain";
const _SINT = "SetIdentityNotificationTopic";
const _SLH = "SentLast24Hours";
const _SNSA = "SNSAction";
const _SNSD = "SNSDestination";
const _SP = "SubjectPart";
const _SRC = "SmtpReplyCode";
const _SRE = "SendRawEmail";
const _SRRP = "SetReceiptRulePosition";
const _SRURL = "SuccessRedirectionURL";
const _ST = "SnsTopic";
const _STE = "SendTemplatedEmail";
const _Sc = "Scope";
const _So = "Source";
const _St = "Status";
const _Su = "Subject";
const _T = "Text";
const _TA = "TopicArn";
const _TARN = "TopicARN";
const _TAe = "TemplateArn";
const _TAo = "ToAddresses";
const _TC = "TemplateContent";
const _TD = "TemplateData";
const _TM = "TemplatesMetadata";
const _TN = "TemplateName";
const _TO = "TrackingOptions";
const _TP = "TlsPolicy";
const _TPe = "TextPart";
const _TRT = "TestRenderTemplate";
const _TS = "TemplateSubject";
const _Ta = "Tags";
const _Te = "Template";
const _Ti = "Timestamp";
const _To = "Topic";
const _UASE = "UpdateAccountSendingEnabled";
const _UCSED = "UpdateConfigurationSetEventDestination";
const _UCSRME = "UpdateConfigurationSetReputationMetricsEnabled";
const _UCSSE = "UpdateConfigurationSetSendingEnabled";
const _UCSTO = "UpdateConfigurationSetTrackingOptions";
const _UCVET = "UpdateCustomVerificationEmailTemplate";
const _URR = "UpdateReceiptRule";
const _UT = "UpdateTemplate";
const _V = "Version";
const _VA = "VerificationAttributes";
const _VDD = "VerifyDomainDkim";
const _VDI = "VerifyDomainIdentity";
const _VEA = "VerifyEmailAddress";
const _VEAe = "VerifiedEmailAddresses";
const _VEI = "VerifyEmailIdentity";
const _VS = "VerificationStatus";
const _VT = "VerificationToken";
const _Va = "Value";
const _WA = "WorkmailAction";
const _e = "entry";
const _m = "message";
const _me = "member";
const buildFormUrlencodedString = (formEntries) => Object.entries(formEntries)
    .map(([key, value]) => __extendedEncodeURIComponent(key) + "=" + __extendedEncodeURIComponent(value))
    .join("&");
const loadQueryErrorCode = (output, data) => {
    if (data.Error?.Code !== undefined) {
        return data.Error.Code;
    }
    if (output.statusCode == 404) {
        return "NotFound";
    }
};
