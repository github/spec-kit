# Java代码审查规范

**Author:** 皮皮芳

---

## 1. 项目强制规范 (⚠️ 必须遵守)

### 1.1 循环调用禁止 🔴

**规则**: 严禁在循环中进行数据库查询或外部接口调用,必须使用批量操作。

**错误示例:**
```java
// ❌ 严重问题: 循环查询数据库 (N+1问题)
List<Order> orders = orderService.getOrders();
for (Order order : orders) {
    // 每次循环都查询一次数据库!
    User user = userMapper.selectById(order.getUserId());
    order.setUserName(user.getName());
}

// ❌ 严重问题: 循环调用外部接口
for (String productId : productIds) {
    // 每次循环都调用一次远程接口!
    ProductDTO product = productFeignClient.getById(productId);
    // 处理逻辑...
}
```

**正确示例:**
```java
// ✅ 正确: 批量查询数据库
List<Order> orders = orderService.getOrders();
List<Long> userIds = orders.stream()
    .map(Order::getUserId)
    .distinct()
    .collect(Collectors.toList());
Map<Long, User> userMap = userMapper.selectByIds(userIds).stream()
    .collect(Collectors.toMap(User::getId, u -> u));
orders.forEach(order -> {
    User user = userMap.get(order.getUserId());
    if (user != null) {
        order.setUserName(user.getName());
    }
});

// ✅ 正确: 批量调用外部接口
List<ProductDTO> products = productFeignClient.batchGetByIds(productIds);
Map<String, ProductDTO> productMap = products.stream()
    .collect(Collectors.toMap(ProductDTO::getId, p -> p));
```

**批量操作阈值**: 当需要查询/调用的数量 ≥ 3 时,必须使用批量操作。

---

### 1.2 大事务限制 🟡

**规则**: 事务范围应尽可能小,避免长事务影响数据库性能和锁竞争。

**限制标准:**
- 单个事务执行时间 < 3秒
- 单个事务涉及表数量 < 5个
- 避免在事务中调用外部接口(网络不确定性)
- 避免在事务中进行大量计算

**错误示例:**
```java
// ❌ 大事务: 包含外部接口调用
@Transactional
public void processOrder(Order order) {
    orderMapper.insert(order);
    // 事务中调用外部接口 - 危险!
    PaymentResult result = paymentFeignClient.pay(order.getId());
    if (result.isSuccess()) {
        order.setStatus("PAID");
        orderMapper.update(order);
    }
}
```

**正确示例:**
```java
// ✅ 正确: 缩小事务范围
public void processOrder(Order order) {
    // 先调用外部接口(事务外)
    PaymentResult result = paymentFeignClient.pay(order.getId());
    
    // 事务仅包含数据库操作
    if (result.isSuccess()) {
        updateOrderStatus(order.getId(), "PAID");
    }
}

@Transactional
private void updateOrderStatus(Long orderId, String status) {
    Order order = new Order();
    order.setId(orderId);
    order.setStatus(status);
    orderMapper.update(order);
}
```

---

### 1.3 跨模块调用审查要点 🟡

**规则**: 涉及Feign/HTTP跨模块调用时,必须追踪到被调用方的实现代码进行审查。

**审查清单:**
- [ ] 被调用方法是否存在循环数据库查询?
- [ ] 被调用方法的事务传播行为是否正确?
- [ ] 被调用方法的异常处理是否会影响调用方?
- [ ] 是否存在循环依赖或调用链过长(>5层)?
- [ ] 跨模块调用的超时配置是否合理?

**示例:**
```java
// 调用方: op-order模块
@PostMapping("/api/order/create")
public Result createOrder(@RequestBody OrderDTO orderDTO) {
    // Feign调用 - 需要追踪到被调用方实现
    return overseasOrderFeignClient.create(orderDTO);
}

// 被调用方: oversea-op-order模块
// ⚠️ 必须审查这个实现!
@Override
public Result create(OrderDTO orderDTO) {
    // 检查是否有循环调用、大事务等问题
    // ...
}
```

---

## 2. Spring Boot审查要点

### 2.1 依赖注入
- 优先使用构造器注入,避免字段注入
- `@Autowired(required=false)` 谨慎使用
- 避免循环依赖

### 2.2 事务管理
- `@Transactional` 传播行为: 
  - 默认`REQUIRED`适用于大多数场景
  - `REQUIRES_NEW`需谨慎(会挂起外层事务)
  - 避免在Controller层使用事务
- 事务方法不能是`private`(Spring AOP限制)
- 同类内部调用不会触发事务(需通过代理调用)

### 2.3 参数校验
- 使用`@Valid`或`@Validated`进行参数校验
- 自定义校验规则使用`@Constraint`注解
- Controller层统一异常处理捕获校验异常

---

## 3. MyBatis审查要点

### 3.1 SQL性能
- 避免`SELECT *`,明确指定需要的字段
- 合理使用索引,检查`WHERE`条件字段是否有索引
- 复杂查询使用`EXPLAIN`分析执行计划
- 避免在SQL中使用函数(破坏索引)

### 3.2 批量操作
- 使用`<foreach>`实现批量插入/更新
- 批量操作数量建议 ≤ 1000条(分批处理)
- 使用`batchInsert`/`batchUpdate`方法命名

### 3.3 SQL注入防护
- 使用`#{}`参数绑定,避免`${}`字符串拼接
- 动态表名/字段名场景需严格校验

---

## 4. 通用审查维度 (检查清单)

### 代码质量
- [ ] 命名清晰有意义
- [ ] 代码简洁无冗余
- [ ] 关键逻辑有注释

### 设计与架构
- [ ] 单一职责原则
- [ ] 依赖抽象而非具体实现
- [ ] 设计模式使用恰当

### 性能优化
- [ ] 算法复杂度合理
- [ ] 无N+1查询
- [ ] 缓存策略正确

### 安全性
- [ ] 输入验证充分
- [ ] 无SQL注入风险
- [ ] 敏感信息加密

### 异常处理
- [ ] 异常捕获合理(不捕获过于宽泛的异常)
- [ ] 异常日志记录完整
- [ ] 错误提示友好

### 日志规范
- [ ] 日志级别恰当(DEBUG/INFO/WARN/ERROR)
- [ ] 关键操作有日志记录
- [ ] 日志不包含敏感信息

### 测试
- [ ] 关键逻辑有单元测试
- [ ] 边界条件已考虑

---

## 5. 审查范围与原则

### 聚焦变更原则
⚠️ 审查应聚焦于本次提交的代码变更:

**主要关注点:**
- ✅ 本次提交直接修改的代码
- ✅ 与修改代码直接相关的调用链(包括跨模块)
- ✅ 受影响的接口契约和数据流

**不要过度延伸:**
- ❌ 对整个项目进行全面审查
- ❌ 审查与本次修改无关的历史遗留问题

**审查边界示例:**
```
修改Service方法 → 审查调用该方法的Controller和被调用的DAO ✅
修改数据库查询 → 审查相关索引和查询性能 ✅
修改异常处理 → 审查异常传播链路 ✅
但不审查完全独立的其他模块 ❌
```

### 区分新旧问题
- 优先关注**本次提交新引入**的问题
- 历史遗留问题需明确标注为"历史问题"
- 每个问题必须关联到具体的commit hash

---

## 6. 问题分级标准

### 🔴 严重问题 (必须修复)
**示例:**
- 循环中查询数据库或调用外部接口
- SQL注入漏洞
- 事务使用错误导致数据不一致
- 潜在的NPE(空指针异常)
- 死锁风险

### 🟡 一般问题 (建议修复)
**示例:**
- 代码可读性差
- 缺少必要的日志
- 异常处理不完善
- 命名不规范

### 🔵 优化建议 (可选)
**示例:**
- 更优雅的实现方式
- 性能优化空间
- 代码结构改进

---

## 附录: 代码示例格式规范

提供修复建议时使用对比格式:

```java
// ❌ 问题代码
public void badExample() {
    // 问题实现
}

// ✅ 修复方案
public void goodExample() {
    // 正确实现
}
```
