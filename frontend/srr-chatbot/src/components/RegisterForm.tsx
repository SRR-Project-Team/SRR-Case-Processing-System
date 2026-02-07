import React from 'react';
import './RegisterForm.css'

// 子组件只接收 props，不定义任何逻辑
interface RegisterFormProps {
  formValues: {
    username: string;
    email: string;
    phone: string;
    password: string;
    confirmPassword: string;
  };
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRegister: () => void;
  isRegisterLoading: boolean;
}

const RegisterForm: React.FC<RegisterFormProps> = ({
  formValues,
  onInputChange,
  onRegister,
  isRegisterLoading
}) => {

  const backToLogin = () => {
    window.location.href = '/login';
  }

  return (
    <div className="register-container">
      {/* 表单标题 */}
      <h2 className="register-title">User Registration</h2>
      
      <form className="register-form">
        {/* 用户名输入框 */}
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input 
            type="text" 
            id="username" 
            className="form-input" 
            placeholder="Username"
            maxLength={10}
            onChange={onInputChange}
            name='username'
            value={formValues.username}
          />
        </div>

        {/* 邮箱输入框 */}
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input 
            type="email" 
            id="email" 
            className="form-input" 
            placeholder="Email"
            onChange={onInputChange}
            name='email'
            value={formValues.email}
          />
        </div>

        {/* 电话号码输入框 */}
        <div className="form-group">
          <label htmlFor="phone">Phone-Number (Hong Kong) </label>
          <input 
            type="tel" 
            id="phone" 
            className="form-input" 
            placeholder="Phone-Number"
            onChange={onInputChange}
            name='phone'
            value={formValues.phone}
          />
        </div>

        {/* 密码输入框 */}
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input 
            type="password" 
            id="password" 
            className="form-input" 
            placeholder="Password"
            onChange={onInputChange}
            name='password'
            value={formValues.password}
          />
        </div>

        {/* 确认密码输入框 */}
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm-Password</label>
          <input 
            type="password" 
            id="confirmPassword" 
            className="form-input" 
            placeholder="Confirm-Password"
            onChange={onInputChange}
            name='confirmPassword'
            value={formValues.confirmPassword}
          />
        </div>

        {/* 确认按钮 */}
        <button type="button" className="submit-btn" onClick={onRegister} disabled={isRegisterLoading}>Register</button>

        {/* 登陆界面跳转按钮 */}
        <div className="register-back-to-login" onClick={backToLogin}>
            Log In
        </div>
      </form>
    </div>
  );
};

export default RegisterForm;