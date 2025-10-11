import { createAggregatedClient } from "@smithy/smithy-client";
import { CloneReceiptRuleSetCommand, } from "./commands/CloneReceiptRuleSetCommand";
import { CreateConfigurationSetCommand, } from "./commands/CreateConfigurationSetCommand";
import { CreateConfigurationSetEventDestinationCommand, } from "./commands/CreateConfigurationSetEventDestinationCommand";
import { CreateConfigurationSetTrackingOptionsCommand, } from "./commands/CreateConfigurationSetTrackingOptionsCommand";
import { CreateCustomVerificationEmailTemplateCommand, } from "./commands/CreateCustomVerificationEmailTemplateCommand";
import { CreateReceiptFilterCommand, } from "./commands/CreateReceiptFilterCommand";
import { CreateReceiptRuleCommand, } from "./commands/CreateReceiptRuleCommand";
import { CreateReceiptRuleSetCommand, } from "./commands/CreateReceiptRuleSetCommand";
import { CreateTemplateCommand, } from "./commands/CreateTemplateCommand";
import { DeleteConfigurationSetCommand, } from "./commands/DeleteConfigurationSetCommand";
import { DeleteConfigurationSetEventDestinationCommand, } from "./commands/DeleteConfigurationSetEventDestinationCommand";
import { DeleteConfigurationSetTrackingOptionsCommand, } from "./commands/DeleteConfigurationSetTrackingOptionsCommand";
import { DeleteCustomVerificationEmailTemplateCommand, } from "./commands/DeleteCustomVerificationEmailTemplateCommand";
import { DeleteIdentityCommand, } from "./commands/DeleteIdentityCommand";
import { DeleteIdentityPolicyCommand, } from "./commands/DeleteIdentityPolicyCommand";
import { DeleteReceiptFilterCommand, } from "./commands/DeleteReceiptFilterCommand";
import { DeleteReceiptRuleCommand, } from "./commands/DeleteReceiptRuleCommand";
import { DeleteReceiptRuleSetCommand, } from "./commands/DeleteReceiptRuleSetCommand";
import { DeleteTemplateCommand, } from "./commands/DeleteTemplateCommand";
import { DeleteVerifiedEmailAddressCommand, } from "./commands/DeleteVerifiedEmailAddressCommand";
import { DescribeActiveReceiptRuleSetCommand, } from "./commands/DescribeActiveReceiptRuleSetCommand";
import { DescribeConfigurationSetCommand, } from "./commands/DescribeConfigurationSetCommand";
import { DescribeReceiptRuleCommand, } from "./commands/DescribeReceiptRuleCommand";
import { DescribeReceiptRuleSetCommand, } from "./commands/DescribeReceiptRuleSetCommand";
import { GetAccountSendingEnabledCommand, } from "./commands/GetAccountSendingEnabledCommand";
import { GetCustomVerificationEmailTemplateCommand, } from "./commands/GetCustomVerificationEmailTemplateCommand";
import { GetIdentityDkimAttributesCommand, } from "./commands/GetIdentityDkimAttributesCommand";
import { GetIdentityMailFromDomainAttributesCommand, } from "./commands/GetIdentityMailFromDomainAttributesCommand";
import { GetIdentityNotificationAttributesCommand, } from "./commands/GetIdentityNotificationAttributesCommand";
import { GetIdentityPoliciesCommand, } from "./commands/GetIdentityPoliciesCommand";
import { GetIdentityVerificationAttributesCommand, } from "./commands/GetIdentityVerificationAttributesCommand";
import { GetSendQuotaCommand, } from "./commands/GetSendQuotaCommand";
import { GetSendStatisticsCommand, } from "./commands/GetSendStatisticsCommand";
import { GetTemplateCommand } from "./commands/GetTemplateCommand";
import { ListConfigurationSetsCommand, } from "./commands/ListConfigurationSetsCommand";
import { ListCustomVerificationEmailTemplatesCommand, } from "./commands/ListCustomVerificationEmailTemplatesCommand";
import { ListIdentitiesCommand, } from "./commands/ListIdentitiesCommand";
import { ListIdentityPoliciesCommand, } from "./commands/ListIdentityPoliciesCommand";
import { ListReceiptFiltersCommand, } from "./commands/ListReceiptFiltersCommand";
import { ListReceiptRuleSetsCommand, } from "./commands/ListReceiptRuleSetsCommand";
import { ListTemplatesCommand, } from "./commands/ListTemplatesCommand";
import { ListVerifiedEmailAddressesCommand, } from "./commands/ListVerifiedEmailAddressesCommand";
import { PutConfigurationSetDeliveryOptionsCommand, } from "./commands/PutConfigurationSetDeliveryOptionsCommand";
import { PutIdentityPolicyCommand, } from "./commands/PutIdentityPolicyCommand";
import { ReorderReceiptRuleSetCommand, } from "./commands/ReorderReceiptRuleSetCommand";
import { SendBounceCommand } from "./commands/SendBounceCommand";
import { SendBulkTemplatedEmailCommand, } from "./commands/SendBulkTemplatedEmailCommand";
import { SendCustomVerificationEmailCommand, } from "./commands/SendCustomVerificationEmailCommand";
import { SendEmailCommand } from "./commands/SendEmailCommand";
import { SendRawEmailCommand, } from "./commands/SendRawEmailCommand";
import { SendTemplatedEmailCommand, } from "./commands/SendTemplatedEmailCommand";
import { SetActiveReceiptRuleSetCommand, } from "./commands/SetActiveReceiptRuleSetCommand";
import { SetIdentityDkimEnabledCommand, } from "./commands/SetIdentityDkimEnabledCommand";
import { SetIdentityFeedbackForwardingEnabledCommand, } from "./commands/SetIdentityFeedbackForwardingEnabledCommand";
import { SetIdentityHeadersInNotificationsEnabledCommand, } from "./commands/SetIdentityHeadersInNotificationsEnabledCommand";
import { SetIdentityMailFromDomainCommand, } from "./commands/SetIdentityMailFromDomainCommand";
import { SetIdentityNotificationTopicCommand, } from "./commands/SetIdentityNotificationTopicCommand";
import { SetReceiptRulePositionCommand, } from "./commands/SetReceiptRulePositionCommand";
import { TestRenderTemplateCommand, } from "./commands/TestRenderTemplateCommand";
import { UpdateAccountSendingEnabledCommand, } from "./commands/UpdateAccountSendingEnabledCommand";
import { UpdateConfigurationSetEventDestinationCommand, } from "./commands/UpdateConfigurationSetEventDestinationCommand";
import { UpdateConfigurationSetReputationMetricsEnabledCommand, } from "./commands/UpdateConfigurationSetReputationMetricsEnabledCommand";
import { UpdateConfigurationSetSendingEnabledCommand, } from "./commands/UpdateConfigurationSetSendingEnabledCommand";
import { UpdateConfigurationSetTrackingOptionsCommand, } from "./commands/UpdateConfigurationSetTrackingOptionsCommand";
import { UpdateCustomVerificationEmailTemplateCommand, } from "./commands/UpdateCustomVerificationEmailTemplateCommand";
import { UpdateReceiptRuleCommand, } from "./commands/UpdateReceiptRuleCommand";
import { UpdateTemplateCommand, } from "./commands/UpdateTemplateCommand";
import { VerifyDomainDkimCommand, } from "./commands/VerifyDomainDkimCommand";
import { VerifyDomainIdentityCommand, } from "./commands/VerifyDomainIdentityCommand";
import { VerifyEmailAddressCommand, } from "./commands/VerifyEmailAddressCommand";
import { VerifyEmailIdentityCommand, } from "./commands/VerifyEmailIdentityCommand";
import { SESClient } from "./SESClient";
const commands = {
    CloneReceiptRuleSetCommand,
    CreateConfigurationSetCommand,
    CreateConfigurationSetEventDestinationCommand,
    CreateConfigurationSetTrackingOptionsCommand,
    CreateCustomVerificationEmailTemplateCommand,
    CreateReceiptFilterCommand,
    CreateReceiptRuleCommand,
    CreateReceiptRuleSetCommand,
    CreateTemplateCommand,
    DeleteConfigurationSetCommand,
    DeleteConfigurationSetEventDestinationCommand,
    DeleteConfigurationSetTrackingOptionsCommand,
    DeleteCustomVerificationEmailTemplateCommand,
    DeleteIdentityCommand,
    DeleteIdentityPolicyCommand,
    DeleteReceiptFilterCommand,
    DeleteReceiptRuleCommand,
    DeleteReceiptRuleSetCommand,
    DeleteTemplateCommand,
    DeleteVerifiedEmailAddressCommand,
    DescribeActiveReceiptRuleSetCommand,
    DescribeConfigurationSetCommand,
    DescribeReceiptRuleCommand,
    DescribeReceiptRuleSetCommand,
    GetAccountSendingEnabledCommand,
    GetCustomVerificationEmailTemplateCommand,
    GetIdentityDkimAttributesCommand,
    GetIdentityMailFromDomainAttributesCommand,
    GetIdentityNotificationAttributesCommand,
    GetIdentityPoliciesCommand,
    GetIdentityVerificationAttributesCommand,
    GetSendQuotaCommand,
    GetSendStatisticsCommand,
    GetTemplateCommand,
    ListConfigurationSetsCommand,
    ListCustomVerificationEmailTemplatesCommand,
    ListIdentitiesCommand,
    ListIdentityPoliciesCommand,
    ListReceiptFiltersCommand,
    ListReceiptRuleSetsCommand,
    ListTemplatesCommand,
    ListVerifiedEmailAddressesCommand,
    PutConfigurationSetDeliveryOptionsCommand,
    PutIdentityPolicyCommand,
    ReorderReceiptRuleSetCommand,
    SendBounceCommand,
    SendBulkTemplatedEmailCommand,
    SendCustomVerificationEmailCommand,
    SendEmailCommand,
    SendRawEmailCommand,
    SendTemplatedEmailCommand,
    SetActiveReceiptRuleSetCommand,
    SetIdentityDkimEnabledCommand,
    SetIdentityFeedbackForwardingEnabledCommand,
    SetIdentityHeadersInNotificationsEnabledCommand,
    SetIdentityMailFromDomainCommand,
    SetIdentityNotificationTopicCommand,
    SetReceiptRulePositionCommand,
    TestRenderTemplateCommand,
    UpdateAccountSendingEnabledCommand,
    UpdateConfigurationSetEventDestinationCommand,
    UpdateConfigurationSetReputationMetricsEnabledCommand,
    UpdateConfigurationSetSendingEnabledCommand,
    UpdateConfigurationSetTrackingOptionsCommand,
    UpdateCustomVerificationEmailTemplateCommand,
    UpdateReceiptRuleCommand,
    UpdateTemplateCommand,
    VerifyDomainDkimCommand,
    VerifyDomainIdentityCommand,
    VerifyEmailAddressCommand,
    VerifyEmailIdentityCommand,
};
export class SES extends SESClient {
}
createAggregatedClient(commands, SES);
