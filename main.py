import pyxel

class App:
    def __init__(self):
        pyxel.init(160, 120, title="Shooting Game")
        # リソースファイルの読み込み
        pyxel.load("assets.pyxres")
        self.reset_game()
        pyxel.run(self.update, self.draw)
    
    def reset_game(self):
        # プレイヤーの初期設定
        self.player_x = 20
        self.player_y = 60
        self.player_speed = 2
        self.lives = 3
        self.is_alive = True
        self.explosion_timer = 0
        self.invincible_timer = 0
        self.shoot_timer = 0  # 連射用のタイマーを追加
        
        # ゲームの状態
        self.game_over = False
        self.game_clear = False
        self.score = 0
        
        # オブジェクトのリスト
        self.bullets = []
        self.enemies = []
        self.particles = []  # 爆発エフェクト用
        self.boss = None
        self.boss_bullets = []
        
        # タイマー
        self.enemy_timer = 0
        self.boss_timer = 0
    
    def update(self):
        if self.game_over or self.game_clear:
            if pyxel.btnp(pyxel.KEY_R):
                self.reset_game()
            return
        
        if self.is_alive:
            # プレイヤーの移動
            if pyxel.btn(pyxel.KEY_UP):
                self.player_y = max(self.player_y - self.player_speed, 0)
            if pyxel.btn(pyxel.KEY_DOWN):
                self.player_y = min(self.player_y + self.player_speed, pyxel.height - 8)
            if pyxel.btn(pyxel.KEY_LEFT):
                self.player_x = max(self.player_x - self.player_speed, 0)
            if pyxel.btn(pyxel.KEY_RIGHT):
                self.player_x = min(self.player_x + self.player_speed, pyxel.width - 8)
            
            # 弾の発射（連射対応）
            if pyxel.btn(pyxel.KEY_SPACE):
                self.shoot_timer += 1
                if self.shoot_timer == 1 or self.shoot_timer % 5 == 0:  # 初回か10フレームごとに発射
                    self.bullets.append({
                        "x": self.player_x + 8,
                        "y": self.player_y + 3,
                        "speed": 4
                    })
            else:
                self.shoot_timer = 0  # スペースキーを離したらタイマーをリセット
        
        # 無敵時間の更新
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        # ボスの出現判定
        if not self.boss and self.score == 10:  # 中ボス
            self.spawn_boss("mid")
        elif not self.boss and self.score == 30:  # ラスボス
            self.spawn_boss("final")
        
        # ボスの更新
        if self.boss:
            self.update_boss()
        else:
            # 通常の敵の生成（ボス戦では出現しない）
            self.enemy_timer += 1
            if self.enemy_timer >= 30:
                self.enemies.append({
                    "x": pyxel.width,
                    "y": pyxel.rndi(0, pyxel.height - 8),
                    "speed": pyxel.rndf(1, 2)
                })
                self.enemy_timer = 0
        
        # 弾の移動
        for bullet in self.bullets[:]:
            bullet["x"] += bullet["speed"]
            if bullet["x"] > pyxel.width:
                self.bullets.remove(bullet)
        
        # ボスの弾の移動
        for bullet in self.boss_bullets[:]:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]
            if (bullet["x"] < -8 or bullet["x"] > pyxel.width + 8 or
                bullet["y"] < -8 or bullet["y"] > pyxel.height + 8):
                self.boss_bullets.remove(bullet)
        
        # 敵の生成
        self.enemy_timer += 1
        if self.enemy_timer >= 30 and not self.boss:
            self.enemies.append({
                "x": pyxel.width,
                "y": pyxel.rndi(0, pyxel.height - 8),
                "speed": pyxel.rndf(1, 2)
            })
            self.enemy_timer = 0
        
        # 敵の移動
        for enemy in self.enemies[:]:
            enemy["x"] -= enemy["speed"]
            if enemy["x"] < -8:
                self.enemies.remove(enemy)
        
        # パーティクルの更新
        for particle in self.particles[:]:
            particle["life"] -= 1
            particle["x"] += particle["dx"]
            particle["y"] += particle["dy"]
            if particle["life"] <= 0:
                self.particles.remove(particle)
        
        # 当たり判定
        if self.is_alive and self.invincible_timer <= 0:
            # プレイヤーと敵の当たり判定
            for enemy in self.enemies[:]:
                if (self.player_x < enemy["x"] + 8 and
                    self.player_x + 8 > enemy["x"] and
                    self.player_y < enemy["y"] + 8 and
                    self.player_y + 8 > enemy["y"]):
                    self.create_explosion(self.player_x + 4, self.player_y + 4)
                    self.is_alive = False
                    self.explosion_timer = 30
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                    break
        
            # プレイヤーとボスの弾の当たり判定
            for bullet in self.boss_bullets[:]:
                if (self.player_x < bullet["x"] + 4 and
                    self.player_x + 8 > bullet["x"] and
                    self.player_y < bullet["y"] + 4 and
                    self.player_y + 8 > bullet["y"]):
                    self.create_explosion(self.player_x + 4, self.player_y + 4)
                    self.is_alive = False
                    self.explosion_timer = 30
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                    break
        
        # プレイヤーの弾とボスの当たり判定
        if self.boss:
            for bullet in self.bullets[:]:
                if (bullet["x"] < self.boss["x"] + self.boss["width"] and
                    bullet["x"] + 2 > self.boss["x"] and
                    bullet["y"] < self.boss["y"] + self.boss["height"] and
                    bullet["y"] + 2 > self.boss["y"]):
                    self.create_explosion(bullet["x"], bullet["y"])
                    self.bullets.remove(bullet)
                    self.boss["hp"] -= 1
                    if self.boss["hp"] <= 0:
                        self.create_explosion(self.boss["x"] + self.boss["width"]/2,
                                           self.boss["y"] + self.boss["height"]/2)
                        self.score += self.boss["score"]
                        self.boss = None
                        if self.score >= 30:  # ラスボスを倒した場合
                            self.game_clear = True
                    break
        
        # プレイヤーの弾と敵の当たり判定
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if (bullet["x"] < enemy["x"] + 8 and
                    bullet["x"] + 2 > enemy["x"] and
                    bullet["y"] < enemy["y"] + 8 and
                    bullet["y"] + 2 > enemy["y"]):
                    self.create_explosion(enemy["x"] + 4, enemy["y"] + 4)
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                    self.score += 1
                    break
        
        # プレイヤーの復活
        if not self.is_alive and not self.game_over:
            self.explosion_timer -= 1
            if self.explosion_timer <= 0:
                self.is_alive = True
                self.player_x = 20
                self.player_y = 60
                self.invincible_timer = 60  # 60フレーム（2秒）の無敵時間
    
    def create_explosion(self, x, y):
        for _ in range(10):
            angle = pyxel.rndf(0, 6.28)
            speed = pyxel.rndf(0.5, 2)
            self.particles.append({
                "x": x,
                "y": y,
                "dx": speed * pyxel.cos(angle),
                "dy": speed * pyxel.sin(angle),
                "life": 30,
                "color": pyxel.rndi(8, 10)
            })
    
    def spawn_boss(self, boss_type):
        if boss_type == "mid":
            self.boss = {
                "type": "mid",
                "x": pyxel.width - 40,  # 少し左に配置
                "y": pyxel.height // 2 - 8,
                "width": 16,
                "height": 16,
                "hp": 20,
                "score": 10,
                "pattern": 0,
                "move_timer": 0,
                "initial_x": pyxel.width - 40  # 初期位置も調整
            }
        else:  # final boss
            self.boss = {
                "type": "final",
                "x": pyxel.width - 48,  # 少し左に配置
                "y": pyxel.height // 2 - 8,
                "width": 16,
                "height": 16,
                "hp": 40,
                "score": 20,
                "pattern": 0,
                "move_timer": 0,
                "attack_phase": 0,
                "phase_timer": 0,
                "initial_x": pyxel.width - 48,  # 初期位置も調整
                "target_y": pyxel.height // 2 - 8
            }
        self.boss_timer = 0

    def update_boss(self):
        boss = self.boss
        self.boss_timer += 1
        
        # ボスの移動パターン
        boss["move_timer"] += 1
        if boss["type"] == "mid":
            # 中ボスの移動パターン（変更なし）
            boss["x"] = boss["initial_x"] + pyxel.sin(boss["move_timer"] * 0.05) * 20
            boss["y"] = pyxel.height/2 - 8 + pyxel.sin(boss["move_timer"] * 0.1) * 30
        else:
            # ラスボスの複雑な移動パターン
            boss["phase_timer"] += 1
            
            # 180フレームごとに攻撃フェーズを変更
            if boss["phase_timer"] >= 180:
                boss["attack_phase"] = (boss["attack_phase"] + 1) % 4
                boss["phase_timer"] = 0
                # 新しい目標位置を設定
                if boss["attack_phase"] == 0:
                    boss["target_y"] = pyxel.height // 2 - 8
                else:
                    boss["target_y"] = pyxel.rndi(16, pyxel.height - 32)
            
            # フェーズに応じた移動パターン
            if boss["attack_phase"] == 0:
                # 8の字移動（画面内に収まるように調整）
                boss["x"] = boss["initial_x"] + pyxel.sin(boss["move_timer"] * 0.05) * 20
                boss["y"] = boss["target_y"] + pyxel.sin(boss["move_timer"] * 0.1) * 30
            elif boss["attack_phase"] == 1:
                # ジグザグ移動（画面内に収まるように調整）
                boss["x"] = boss["initial_x"] + pyxel.sin(boss["move_timer"] * 0.1) * 15
                boss["y"] = boss["target_y"] + pyxel.cos(boss["move_timer"] * 0.2) * 25
            elif boss["attack_phase"] == 2:
                # 円運動（画面内に収まるように調整）
                angle = boss["move_timer"] * 0.05
                boss["x"] = boss["initial_x"] + pyxel.cos(angle) * 15
                boss["y"] = boss["target_y"] + pyxel.sin(angle) * 25
            else:
                # 急速な直線移動（画面内に収まるように調整）
                boss["x"] = boss["initial_x"] + pyxel.sin(boss["move_timer"] * 0.15) * 10
                target_offset = pyxel.sin(boss["move_timer"] * 0.1) * 30
                boss["y"] = boss["target_y"] + target_offset
        
        # ボスの攻撃パターン
        if self.boss_timer >= 30:
            self.boss_timer = 0
            if boss["type"] == "mid":
                # 中ボスの攻撃
                for angle in [-0.2, 0, 0.2]:
                    self.boss_bullets.append({
                        "x": boss["x"],
                        "y": boss["y"] + boss["height"]/2,
                        "dx": -3 * pyxel.cos(angle),
                        "dy": 3 * pyxel.sin(angle)
                    })
            else:
                # ラスボスの攻撃（フェーズに応じて変化）
                if boss["attack_phase"] == 0:
                    # 扇状の弾幕
                    for i in range(8):
                        angle = i * 0.785 + pyxel.sin(boss["move_timer"] * 0.1)
                        self.boss_bullets.append({
                            "x": boss["x"] + boss["width"]/2,
                            "y": boss["y"] + boss["height"]/2,
                            "dx": -4 * pyxel.cos(angle),
                            "dy": 4 * pyxel.sin(angle)
                        })
                elif boss["attack_phase"] == 1:
                    # プレイヤーを狙う3方向弾
                    if self.is_alive:
                        target_angle = pyxel.atan2(
                            self.player_y - boss["y"],
                            self.player_x - boss["x"]
                        )
                        for angle_offset in [-0.3, 0, 0.3]:
                            angle = target_angle + angle_offset
                            self.boss_bullets.append({
                                "x": boss["x"] + boss["width"]/2,
                                "y": boss["y"] + boss["height"]/2,
                                "dx": 4 * pyxel.cos(angle),
                                "dy": 4 * pyxel.sin(angle)
                            })
                elif boss["attack_phase"] == 2:
                    # 螺旋状の弾幕
                    angle = boss["move_timer"] * 0.2
                    for i in range(4):
                        current_angle = angle + i * 1.57  # 90度ずつ
                        self.boss_bullets.append({
                            "x": boss["x"] + boss["width"]/2,
                            "y": boss["y"] + boss["height"]/2,
                            "dx": -3.5 * pyxel.cos(current_angle),
                            "dy": 3.5 * pyxel.sin(current_angle)
                        })
                else:
                    # 全方向ランダム弾
                    for _ in range(6):
                        random_angle = pyxel.rndf(0, 6.28)
                        self.boss_bullets.append({
                            "x": boss["x"] + boss["width"]/2,
                            "y": boss["y"] + boss["height"]/2,
                            "dx": -4 * pyxel.cos(random_angle),
                            "dy": 4 * pyxel.sin(random_angle)
                        })

    def draw(self):
        pyxel.cls(0)
        
        # プレイヤーの描画
        if self.is_alive:
            if self.invincible_timer == 0 or pyxel.frame_count % 4 < 2:
                pyxel.blt(self.player_x, self.player_y, 0, 0, 0, 8, 8, 0)
        
        # 弾の描画
        for bullet in self.bullets:
            pyxel.blt(bullet["x"], bullet["y"], 0, 8, 0, 8, 2, 0)
            
        # 敵の描画
        for enemy in self.enemies:
            pyxel.blt(enemy["x"], enemy["y"], 0, 16, 0, 8, 8, 0)
        
        # ボスの描画
        if self.boss:
            if self.boss["type"] == "mid":
                # 中ボス (40, 0)から16x16
                pyxel.blt(self.boss["x"], self.boss["y"], 0, 40, 0, 16, 16, 0)
            else:
                # ラスボス (24, 0)から16x16
                pyxel.blt(self.boss["x"], self.boss["y"], 0, 24, 0, 16, 16, 0)
            
            # HPバー
            hp_width = (self.boss["width"] * self.boss["hp"]) // (40 if self.boss["type"] == "final" else 20)
            pyxel.rect(self.boss["x"], self.boss["y"] - 5, hp_width, 2, 11)
        
        # ボスの弾の描画
        for bullet in self.boss_bullets:
            pyxel.blt(bullet["x"], bullet["y"], 0, 8, 0, 8, 2, 0)
        
        # パーティクルの描画
        for particle in self.particles:
            pyxel.pset(particle["x"], particle["y"], particle["color"])
        
        # スコアとライフの表示
        pyxel.text(5, 5, f"SCORE: {self.score}", 7)
        pyxel.text(5, 15, f"LIVES: {self.lives}", 7)
        
        # ゲームオーバー/クリア画面
        if self.game_over:
            pyxel.text(60, 50, "GAME OVER", 8)
            pyxel.text(45, 70, "PRESS R TO RESTART", 7)
        elif self.game_clear:
            pyxel.text(60, 50, "GAME CLEAR!", 11)
            pyxel.text(45, 70, "PRESS R TO RESTART", 7)

App()