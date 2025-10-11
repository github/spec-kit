import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  VerifyDomainIdentityRequest,
  VerifyDomainIdentityResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface VerifyDomainIdentityCommandInput
  extends VerifyDomainIdentityRequest {}
export interface VerifyDomainIdentityCommandOutput
  extends VerifyDomainIdentityResponse,
    __MetadataBearer {}
declare const VerifyDomainIdentityCommand_base: {
  new (
    input: VerifyDomainIdentityCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyDomainIdentityCommandInput,
    VerifyDomainIdentityCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: VerifyDomainIdentityCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyDomainIdentityCommandInput,
    VerifyDomainIdentityCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class VerifyDomainIdentityCommand extends VerifyDomainIdentityCommand_base {
  protected static __types: {
    api: {
      input: VerifyDomainIdentityRequest;
      output: VerifyDomainIdentityResponse;
    };
    sdk: {
      input: VerifyDomainIdentityCommandInput;
      output: VerifyDomainIdentityCommandOutput;
    };
  };
}
