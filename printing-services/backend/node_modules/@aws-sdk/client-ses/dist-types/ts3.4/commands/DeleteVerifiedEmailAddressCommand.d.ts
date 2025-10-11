import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteVerifiedEmailAddressRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface DeleteVerifiedEmailAddressCommandInput
  extends DeleteVerifiedEmailAddressRequest {}
export interface DeleteVerifiedEmailAddressCommandOutput
  extends __MetadataBearer {}
declare const DeleteVerifiedEmailAddressCommand_base: {
  new (
    input: DeleteVerifiedEmailAddressCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteVerifiedEmailAddressCommandInput,
    DeleteVerifiedEmailAddressCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: DeleteVerifiedEmailAddressCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    DeleteVerifiedEmailAddressCommandInput,
    DeleteVerifiedEmailAddressCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class DeleteVerifiedEmailAddressCommand extends DeleteVerifiedEmailAddressCommand_base {
  protected static __types: {
    api: {
      input: DeleteVerifiedEmailAddressRequest;
      output: {};
    };
    sdk: {
      input: DeleteVerifiedEmailAddressCommandInput;
      output: DeleteVerifiedEmailAddressCommandOutput;
    };
  };
}
