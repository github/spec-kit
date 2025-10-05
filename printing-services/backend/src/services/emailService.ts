import nodemailer from 'nodemailer'
import { generateVerificationToken } from '@/utils/auth'

// Email transporter configuration
const createTransporter = () => {
  return nodemailer.createTransporter({
    host: process.env.EMAIL_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.EMAIL_PORT || '587'),
    secure: false, // true for 465, false for other ports
    auth: {
      user: process.env.EMAIL_USER,
      pass: process.env.EMAIL_PASS,
    },
  })
}

// Email templates
const getVerificationEmailTemplate = (firstName: string, verificationUrl: string) => {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Verify Your PrintMarket Account</title>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #3b82f6; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f8fafc; }
        .button { 
          display: inline-block; 
          background: #3b82f6; 
          color: white; 
          padding: 12px 30px; 
          text-decoration: none; 
          border-radius: 5px; 
          margin: 20px 0;
        }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 14px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>Welcome to PrintMarket!</h1>
        </div>
        <div class="content">
          <h2>Hi ${firstName},</h2>
          <p>Thank you for joining PrintMarket, Canada's trusted printing services marketplace!</p>
          <p>To complete your registration and start using your account, please verify your email address by clicking the button below:</p>
          <div style="text-align: center;">
            <a href="${verificationUrl}" class="button">Verify Email Address</a>
          </div>
          <p>Or copy and paste this link into your browser:</p>
          <p style="word-break: break-all; color: #3b82f6;">${verificationUrl}</p>
          <p><strong>This link will expire in 24 hours.</strong></p>
          <p>If you didn't create an account with PrintMarket, please ignore this email.</p>
        </div>
        <div class="footer">
          <p>PrintMarket - Connecting Canada's Printing Community</p>
          <p>This is an automated message, please do not reply to this email.</p>
        </div>
      </div>
    </body>
    </html>
  `
}

const getBrokerApprovalTemplate = (firstName: string, companyName: string) => {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Broker Account Approved - PrintMarket</title>
      <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #10b981; color: white; padding: 20px; text-align: center; }
        .content { padding: 30px 20px; background: #f8fafc; }
        .button { 
          display: inline-block; 
          background: #10b981; 
          color: white; 
          padding: 12px 30px; 
          text-decoration: none; 
          border-radius: 5px; 
          margin: 20px 0;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>🎉 Broker Account Approved!</h1>
        </div>
        <div class="content">
          <h2>Congratulations ${firstName}!</h2>
          <p>Your broker account for <strong>${companyName}</strong> has been approved and is now active on PrintMarket.</p>
          <p>You can now:</p>
          <ul>
            <li>Browse and bid on printing requests</li>
            <li>Submit proposals to customers</li>
            <li>Manage your jobs and earnings</li>
            <li>Build your reputation with reviews</li>
          </ul>
          <div style="text-align: center;">
            <a href="${process.env.FRONTEND_URL}/dashboard" class="button">Access Your Dashboard</a>
          </div>
          <p>Welcome to the PrintMarket community!</p>
        </div>
      </div>
    </body>
    </html>
  `
}

// Send verification email
export const sendVerificationEmail = async (
  email: string, 
  firstName: string, 
  userId: string
): Promise<void> => {
  try {
    const transporter = createTransporter()
    const token = generateVerificationToken(userId)
    const verificationUrl = `${process.env.FRONTEND_URL}/verify-email/${token}`
    
    const mailOptions = {
      from: process.env.EMAIL_FROM || '"PrintMarket" <noreply@printmarket.ca>',
      to: email,
      subject: 'Verify Your PrintMarket Account',
      html: getVerificationEmailTemplate(firstName, verificationUrl)
    }

    await transporter.sendMail(mailOptions)
    console.log(`✅ Verification email sent to ${email}`)
  } catch (error) {
    console.error('❌ Failed to send verification email:', error)
    throw new Error('Failed to send verification email')
  }
}

// Send broker approval email
export const sendBrokerApprovalEmail = async (
  email: string,
  firstName: string,
  companyName: string
): Promise<void> => {
  try {
    const transporter = createTransporter()
    
    const mailOptions = {
      from: process.env.EMAIL_FROM || '"PrintMarket" <noreply@printmarket.ca>',
      to: email,
      subject: 'Broker Account Approved - PrintMarket',
      html: getBrokerApprovalTemplate(firstName, companyName)
    }

    await transporter.sendMail(mailOptions)
    console.log(`✅ Broker approval email sent to ${email}`)
  } catch (error) {
    console.error('❌ Failed to send broker approval email:', error)
    throw new Error('Failed to send broker approval email')
  }
}

// Send password reset email (for future use)
export const sendPasswordResetEmail = async (
  email: string,
  firstName: string,
  resetToken: string
): Promise<void> => {
  try {
    const transporter = createTransporter()
    const resetUrl = `${process.env.FRONTEND_URL}/reset-password/${resetToken}`
    
    const mailOptions = {
      from: process.env.EMAIL_FROM || '"PrintMarket" <noreply@printmarket.ca>',
      to: email,
      subject: 'Reset Your PrintMarket Password',
      html: `
        <h2>Password Reset Request</h2>
        <p>Hi ${firstName},</p>
        <p>Click the link below to reset your password:</p>
        <a href="${resetUrl}">Reset Password</a>
        <p>This link expires in 1 hour.</p>
      `
    }

    await transporter.sendMail(mailOptions)
    console.log(`✅ Password reset email sent to ${email}`)
  } catch (error) {
    console.error('❌ Failed to send password reset email:', error)
    throw new Error('Failed to send password reset email')
  }
}

// Test email configuration
export const testEmailConfiguration = async (): Promise<boolean> => {
  try {
    const transporter = createTransporter()
    await transporter.verify()
    console.log('✅ Email configuration is valid')
    return true
  } catch (error) {
    console.error('❌ Email configuration error:', error)
    return false
  }
}
