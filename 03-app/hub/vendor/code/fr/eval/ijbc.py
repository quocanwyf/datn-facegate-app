"""Đánh giá IJB-C 1:1 (verification) và 1:N (open-set identification) — DÙNG NGUYÊN code tham chiếu insightface.

Nguồn (bản gốc nguyên văn lưu ở ``third_party/insightface_ijb/`` để đối chiếu từng dòng):
  [R1] deepinsight/insightface ``recognition/arcface_torch/eval_ijbc.py``
       commit 676b02d8e6e2515433dda9d438b1922094c928ad (lần sửa cuối của file, 23/06/2021; trùng byte với
       master c6c3af7bd2d0a0bf4b78c78437357f3521aa5d52 ngày 05/11/2026).
       https://github.com/deepinsight/insightface/blob/676b02d8e6e2515433dda9d438b1922094c928ad/recognition/arcface_torch/eval_ijbc.py
       → dùng cho 1:1: Embedding (căn chỉnh 5 điểm + ảnh lật), get_image_feature, image2template_feature,
         verification, bảng TPR@FPR (roc_curve).
  [R2] deepinsight/insightface ``recognition/_evaluation_/ijb/ijb_evals.py``
       commit 0ff3ad5bb53028045ad91d2ed841f1570236940a ("Fix IJB 1:N evaluation in ijb_evals.py", 04/09/2021;
       trùng byte với master c6c3af7b).
       https://github.com/deepinsight/insightface/blob/0ff3ad5bb53028045ad91d2ed841f1570236940a/recognition/_evaluation_/ijb/ijb_evals.py
       → dùng cho 1:N: read_IJB_meta_columns_to_int, image2template_feature (nhánh 1:N), evaluation_1N,
         phần thân run_model_test_1N (G1/G2 riêng, TPIR trung bình).
  README trang IJB của insightface nói 1:N dựa trên code của Yuge Huang [8]; repo của Yuge Huang
  (github.com/HuangYG123/DDL) chỉ có README. Script 1:N "chính" của insightface là ``ijb_1n.py``, nhưng script
  đó GỘP G1+G2 thành một gallery và bắt mọi probe phải có trong gallery (gen_mask raise lỗi nếu không) → thực
  chất là closed-set, KHÔNG đo được người lạ. Vì vậy dùng ``evaluation_1N`` của [R2] (cùng thư mục, bản đã sửa
  1:N): đánh giá riêng G1 và G2, probe không có trong gallery = người lạ → open-set đúng protocol NIST.

DANH SÁCH CHỖ SỬA (đánh dấu ``# [S#]`` trong code; ngoài các chỗ này giữ nguyên dòng code gốc):
  [S1] ``np.int`` → ``int``: numpy ≥ 1.24 đã xoá alias ``np.int`` (gọi sẽ lỗi AttributeError). Không đổi ý nghĩa.
  [S2] ``Embedding.__init__`` nhận sẵn backbone của codebase (``fr.backbones``) + device, thay vì
       ``torch.load(prefix)`` + ``get_model`` + ``.cuda()`` + ``DataParallel`` (codebase có kiến trúc/checkpoint riêng,
       chạy 1 GPU). Template 5 điểm ``src`` và hàm ``get`` giữ nguyên.
  [S3] ``forward_db``: ``.cuda()`` → ``.to(device)``; thêm ``.float()`` sau backbone (backbone fp16 của
       codebase trả fp16 ở một số khối) — không đổi phép tính.
  [S4] ``get_image_feature`` nhận backbone/device thay vì đường dẫn model (không phải nạp lại model 2 lần);
       số chiều đặc trưng lấy từ backbone thay vì hằng 1024 (= 2×512 — giống hệt với backbone 512 chiều).
  [S5] Bỏ phần vẽ/in (matplotlib, menpo ``sample_colours_from_colourmap``, PrettyTable) và ``argparse`` toàn cục;
       phần tính TPR@FPR (roc_curve → flipud → chọn FPR gần nhất) đóng gói thành hàm ``tpr_at_fpr_table``,
       giữ nguyên các dòng tính. Phần script chính Step 1–4 (đọc meta → đặc trưng → cờ N1D1F2 → template → điểm)
       đóng gói thành hàm ``evaluate_ijbc`` với cùng thứ tự và cùng cờ; thêm tham số ``max_images`` CHỈ để chạy thử.
  [S6] [R2] ``evaluation_1N``: chỉ bỏ ``print``; thêm trả về số probe mated/non-mated để báo cáo.
       Thân ``run_model_test_1N`` viết thành hàm ``evaluate_1N`` nhận đặc trưng ảnh đã tính sẵn (dùng chung lần trích
       đặc trưng với 1:1), giữ nguyên cờ (flip cộng, không chuẩn hoá ảnh, nhân điểm detector) và cách lấy trung bình G1/G2.
  [S7] ``extract_gallery_prob_data`` của [R2]: bỏ phần lưu/nạp file backup ``.npz``; đọc 3 file meta y hệt.
  Không sửa bất kỳ dòng nào tính template, điểm cosine, ngưỡng, TPR/TPIR.

Bổ sung (KHÔNG thay code gốc, chỉ thêm thông tin để báo cáo):
  - ``safe_tpr_at_fpr``: gọi ``tpr_at_fpr_table`` rồi đánh NaN ở FPR < 1/số cặp âm (không đo được).
  - ``rates_at_learned_threshold``: TAR/FAR (1:1) và FNIR/FPIR (1:N) tại ngưỡng t cho trước (vd. t = b/s học
    được của UniFace) — dùng ``fr.eval.metrics.rates_at_threshold`` đã có unit test.

Lưu ý quy ước tính (để giải thích trước hội đồng):
  - 1:1 [R1]: TPR tại FPR là điểm ROC có FPR GẦN NHẤT với mức yêu cầu (không phải "FPR ≤ mức").
  - 1:N [R2]: ngưỡng = điểm max người lạ thứ ``max(int(N·FPIR) − 1, 0)`` (sắp giảm dần), đúng khi điểm > ngưỡng
    VÀ rank-1 đúng → số người lạ vượt ngưỡng ≈ int(N·FPIR) − 1.
  - Đặc trưng ảnh: emb(ảnh) + emb(ảnh lật), KHÔNG chuẩn hoá, nhân điểm detector (TestMode N1D1F2 của [R1]).
"""
from __future__ import annotations

import os
import timeit
from typing import Dict, Iterable, Optional, Sequence

import cv2
import numpy as np
import pandas as pd
import sklearn.preprocessing
import torch
from skimage import transform as trans
from sklearn.metrics import roc_curve

from .metrics import rates_at_threshold

DEFAULT_FPRS_11 = [10 ** -6, 10 ** -5, 10 ** -4, 10 ** -3, 10 ** -2, 10 ** -1]   # x_labels của [R1]
DEFAULT_FPIRS_1N = [0.01, 0.1]                                                    # Fars mặc định của evaluation_1N [R2]


# =====================================================================================================
# [R1] eval_ijbc.py — Embedding
# =====================================================================================================
class Embedding(object):
    def __init__(self, backbone, device, data_shape=(3, 112, 112), batch_size=1):   # [S2]
        image_size = (112, 112)
        self.image_size = image_size
        self.model = backbone                                                          # [S2]
        self.device = device                                                           # [S2]
        self.model.eval()
        src = np.array([
            [30.2946, 51.6963],
            [65.5318, 51.5014],
            [48.0252, 71.7366],
            [33.5493, 92.3655],
            [62.7299, 92.2041]], dtype=np.float32)
        src[:, 0] += 8.0
        self.src = src
        self.batch_size = batch_size
        self.data_shape = data_shape

    def get(self, rimg, landmark):

        assert landmark.shape[0] == 68 or landmark.shape[0] == 5
        assert landmark.shape[1] == 2
        if landmark.shape[0] == 68:
            landmark5 = np.zeros((5, 2), dtype=np.float32)
            landmark5[0] = (landmark[36] + landmark[39]) / 2
            landmark5[1] = (landmark[42] + landmark[45]) / 2
            landmark5[2] = landmark[30]
            landmark5[3] = landmark[48]
            landmark5[4] = landmark[54]
        else:
            landmark5 = landmark
        tform = trans.SimilarityTransform()
        tform.estimate(landmark5, self.src)
        M = tform.params[0:2, :]
        img = cv2.warpAffine(rimg,
                             M, (self.image_size[1], self.image_size[0]),
                             borderValue=0.0)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_flip = np.fliplr(img)
        img = np.transpose(img, (2, 0, 1))  # 3*112*112, RGB
        img_flip = np.transpose(img_flip, (2, 0, 1))
        input_blob = np.zeros((2, 3, self.image_size[1], self.image_size[0]), dtype=np.uint8)
        input_blob[0] = img
        input_blob[1] = img_flip
        return input_blob

    @torch.no_grad()
    def forward_db(self, batch_data):
        imgs = torch.Tensor(batch_data).to(self.device)                                # [S3]
        imgs.div_(255).sub_(0.5).div_(0.5)
        feat = self.model(imgs).float()                                                # [S3]
        feat = feat.reshape([self.batch_size, 2 * feat.shape[1]])
        return feat.cpu().numpy()


# =====================================================================================================
# [R1] eval_ijbc.py — đọc meta
# =====================================================================================================
def read_template_media_list(path):
    # ijb_meta = np.loadtxt(path, dtype=str)
    ijb_meta = pd.read_csv(path, sep=' ', header=None).values
    templates = ijb_meta[:, 1].astype(int)                                             # [S1]
    medias = ijb_meta[:, 2].astype(int)                                                # [S1]
    return templates, medias


def read_template_pair_list(path):
    # pairs = np.loadtxt(path, dtype=str)
    pairs = pd.read_csv(path, sep=' ', header=None).values
    t1 = pairs[:, 0].astype(int)                                                       # [S1]
    t2 = pairs[:, 1].astype(int)                                                       # [S1]
    label = pairs[:, 2].astype(int)                                                    # [S1]
    return t1, t2, label


# =====================================================================================================
# [R1] eval_ijbc.py — trích đặc trưng ảnh
# =====================================================================================================
def get_image_feature(img_path, files_list, backbone, device, batch_size=128, emb_dim=512):   # [S4]
    data_shape = (3, 112, 112)

    files = files_list
    print('files:', len(files))
    rare_size = len(files) % batch_size
    faceness_scores = []
    batch = 0
    img_feats = np.empty((len(files), 2 * emb_dim), dtype=np.float32)                 # [S4] (gốc: 1024)

    batch_data = np.empty((2 * batch_size, 3, 112, 112))
    embedding = Embedding(backbone, device, data_shape, batch_size)                    # [S4]
    for img_index, each_line in enumerate(files[:len(files) - rare_size]):
        name_lmk_score = each_line.strip().split(' ')
        img_name = os.path.join(img_path, name_lmk_score[0])
        img = cv2.imread(img_name)
        lmk = np.array([float(x) for x in name_lmk_score[1:-1]],
                       dtype=np.float32)
        lmk = lmk.reshape((5, 2))
        input_blob = embedding.get(img, lmk)

        batch_data[2 * (img_index - batch * batch_size)][:] = input_blob[0]
        batch_data[2 * (img_index - batch * batch_size) + 1][:] = input_blob[1]
        if (img_index + 1) % batch_size == 0:
            print('batch', batch)
            img_feats[batch * batch_size:batch * batch_size +
                                         batch_size][:] = embedding.forward_db(batch_data)
            batch += 1
        faceness_scores.append(name_lmk_score[-1])

    batch_data = np.empty((2 * rare_size, 3, 112, 112))
    embedding = Embedding(backbone, device, data_shape, rare_size)                     # [S4]
    for img_index, each_line in enumerate(files[len(files) - rare_size:]):
        name_lmk_score = each_line.strip().split(' ')
        img_name = os.path.join(img_path, name_lmk_score[0])
        img = cv2.imread(img_name)
        lmk = np.array([float(x) for x in name_lmk_score[1:-1]],
                       dtype=np.float32)
        lmk = lmk.reshape((5, 2))
        input_blob = embedding.get(img, lmk)
        batch_data[2 * img_index][:] = input_blob[0]
        batch_data[2 * img_index + 1][:] = input_blob[1]
        if (img_index + 1) % rare_size == 0:
            print('batch', batch)
            img_feats[len(files) -
                      rare_size:][:] = embedding.forward_db(batch_data)
            batch += 1
        faceness_scores.append(name_lmk_score[-1])
    faceness_scores = np.array(faceness_scores).astype(np.float32)
    # img_feats = np.ones( (len(files), 1024), dtype=np.float32) * 0.01
    # faceness_scores = np.ones( (len(files), ), dtype=np.float32 )
    return img_feats, faceness_scores


# =====================================================================================================
# [R1] eval_ijbc.py — template + verification
# =====================================================================================================
def image2template_feature(img_feats=None, templates=None, medias=None):
    # ==========================================================
    # 1. face image feature l2 normalization. img_feats:[number_image x feats_dim]
    # 2. compute media feature.
    # 3. compute template feature.
    # ==========================================================
    unique_templates = np.unique(templates)
    template_feats = np.zeros((len(unique_templates), img_feats.shape[1]))

    for count_template, uqt in enumerate(unique_templates):

        (ind_t,) = np.where(templates == uqt)
        face_norm_feats = img_feats[ind_t]
        face_medias = medias[ind_t]
        unique_medias, unique_media_counts = np.unique(face_medias,
                                                       return_counts=True)
        media_norm_feats = []
        for u, ct in zip(unique_medias, unique_media_counts):
            (ind_m,) = np.where(face_medias == u)
            if ct == 1:
                media_norm_feats += [face_norm_feats[ind_m]]
            else:  # image features from the same video will be aggregated into one feature
                media_norm_feats += [
                    np.mean(face_norm_feats[ind_m], axis=0, keepdims=True)
                ]
        media_norm_feats = np.array(media_norm_feats)
        # media_norm_feats = media_norm_feats / np.sqrt(np.sum(media_norm_feats ** 2, -1, keepdims=True))
        template_feats[count_template] = np.sum(media_norm_feats, axis=0)
        if count_template % 2000 == 0:
            print('Finish Calculating {} template features.'.format(
                count_template))
    # template_norm_feats = template_feats / np.sqrt(np.sum(template_feats ** 2, -1, keepdims=True))
    template_norm_feats = sklearn.preprocessing.normalize(template_feats)
    # print(template_norm_feats.shape)
    return template_norm_feats, unique_templates


def verification(template_norm_feats=None,
                 unique_templates=None,
                 p1=None,
                 p2=None):
    # ==========================================================
    #         Compute set-to-set Similarity Score.
    # ==========================================================
    template2id = np.zeros((max(unique_templates) + 1, 1), dtype=int)
    for count_template, uqt in enumerate(unique_templates):
        template2id[uqt] = count_template

    score = np.zeros((len(p1),))  # save cosine distance between pairs

    total_pairs = np.array(range(len(p1)))
    batchsize = 100000  # small batchsize instead of all pairs in one batch due to the memory limiation
    sublists = [
        total_pairs[i:i + batchsize] for i in range(0, len(p1), batchsize)
    ]
    total_sublists = len(sublists)
    for c, s in enumerate(sublists):
        feat1 = template_norm_feats[template2id[p1[s]]]
        feat2 = template_norm_feats[template2id[p2[s]]]
        similarity_score = np.sum(feat1 * feat2, -1)
        score[s] = similarity_score.flatten()
        if c % 10 == 0:
            print('Finish {}/{} pairs.'.format(c, total_sublists))
    return score


# =====================================================================================================
# [R1] eval_ijbc.py — Step 5: ROC + bảng TPR@FPR                                               [S5]
# =====================================================================================================
def tpr_at_fpr_table(label, scores: Dict[str, np.ndarray], x_labels: Sequence[float] = DEFAULT_FPRS_11):
    """Các dòng tính giữ nguyên Step 5 của [R1]; chỉ bỏ vẽ hình/PrettyTable, trả dict thay vì in."""
    out = {}
    methods = list(scores.keys())
    for method in methods:
        fpr, tpr, _ = roc_curve(label, scores[method])
        fpr = np.flipud(fpr)
        tpr = np.flipud(tpr)  # select largest tpr at same fpr
        tpr_fpr_row = {}
        for fpr_iter in np.arange(len(x_labels)):
            _, min_index = min(
                list(zip(abs(fpr - x_labels[fpr_iter]), range(len(fpr)))))
            tpr_fpr_row[x_labels[fpr_iter]] = float(tpr[min_index])
        out[method] = tpr_fpr_row
    return out


def safe_tpr_at_fpr(label, score, x_labels: Sequence[float] = DEFAULT_FPRS_11) -> Dict[str, float]:
    """Bổ sung: gọi tpr_at_fpr_table rồi đánh NaN ở FPR không đo được (FPR·số cặp âm < 1)."""
    label = np.asarray(label).astype(int)
    n_pos, n_neg = int((label == 1).sum()), int((label == 0).sum())
    row = tpr_at_fpr_table(label, {"m": np.asarray(score)}, x_labels)["m"]
    res = {"n_pos": n_pos, "n_neg": n_neg, "min_measurable_far": (1.0 / n_neg) if n_neg else float("nan")}
    for x in x_labels:
        res[f"tar@far={x:g}"] = row[x] if x * n_neg >= 1 else float("nan")
    return res


# =====================================================================================================
# [R2] ijb_evals.py — 1:N
# =====================================================================================================
def read_IJB_meta_columns_to_int(file_path, columns, sep=" ", skiprows=0, header=None):
    # meta = np.loadtxt(file_path, skiprows=skiprows, delimiter=sep)
    meta = pd.read_csv(file_path, sep=sep, skiprows=skiprows, header=header).values
    return (meta[:, ii].astype("int") for ii in columns)


def extract_gallery_prob_data(meta_dir, subset="IJBC"):                               # [S7]
    if subset == "IJBC":
        gallery_s1_record = os.path.join(meta_dir, "ijbc_1N_gallery_G1.csv")
        gallery_s2_record = os.path.join(meta_dir, "ijbc_1N_gallery_G2.csv")
        probe_mixed_record = os.path.join(meta_dir, "ijbc_1N_probe_mixed.csv")
    else:
        gallery_s1_record = os.path.join(meta_dir, "ijbb_1N_gallery_S1.csv")
        gallery_s2_record = os.path.join(meta_dir, "ijbb_1N_gallery_S2.csv")
        probe_mixed_record = os.path.join(meta_dir, "ijbb_1N_probe_mixed.csv")

    print(">>>> Loading gallery feature...")
    s1_templates, s1_subject_ids = read_IJB_meta_columns_to_int(gallery_s1_record, columns=[0, 1], skiprows=1, sep=",")
    s2_templates, s2_subject_ids = read_IJB_meta_columns_to_int(gallery_s2_record, columns=[0, 1], skiprows=1, sep=",")
    print("s1 gallery: %s, ids: %s, unique: %s" % (s1_templates.shape, s1_subject_ids.shape, np.unique(s1_templates).shape))
    print("s2 gallery: %s, ids: %s, unique: %s" % (s2_templates.shape, s2_subject_ids.shape, np.unique(s2_templates).shape))

    print(">>>> Loading prope feature...")
    probe_mixed_templates, probe_mixed_subject_ids = read_IJB_meta_columns_to_int(
        probe_mixed_record, columns=[0, 1], skiprows=1, sep=","
    )
    print("probe_mixed_templates: %s, unique: %s" % (probe_mixed_templates.shape, np.unique(probe_mixed_templates).shape))
    print("probe_mixed_subject_ids: %s, unique: %s" % (probe_mixed_subject_ids.shape, np.unique(probe_mixed_subject_ids).shape))
    return s1_templates, s1_subject_ids, s2_templates, s2_subject_ids, probe_mixed_templates, probe_mixed_subject_ids


def image2template_feature_1N(img_feats=None, templates=None, medias=None, choose_templates=None, choose_ids=None):
    """[R2] image2template_feature (đổi tên để không trùng hàm của [R1]; bỏ tqdm)."""
    if choose_templates is not None:  # 1:N
        unique_templates, indices = np.unique(choose_templates, return_index=True)
        unique_subjectids = choose_ids[indices]
    else:  # 1:1
        unique_templates = np.unique(templates)
        unique_subjectids = None

    # template_feats = np.zeros((len(unique_templates), img_feats.shape[1]), dtype=img_feats.dtype)
    template_feats = np.zeros((len(unique_templates), img_feats.shape[1]))
    for count_template, uqt in enumerate(unique_templates):
        (ind_t,) = np.where(templates == uqt)
        face_norm_feats = img_feats[ind_t]
        face_medias = medias[ind_t]
        unique_medias, unique_media_counts = np.unique(face_medias, return_counts=True)
        media_norm_feats = []
        for u, ct in zip(unique_medias, unique_media_counts):
            (ind_m,) = np.where(face_medias == u)
            if ct == 1:
                media_norm_feats += [face_norm_feats[ind_m]]
            else:  # image features from the same video will be aggregated into one feature
                media_norm_feats += [np.mean(face_norm_feats[ind_m], 0, keepdims=True)]
        media_norm_feats = np.array(media_norm_feats)
        # media_norm_feats = media_norm_feats / np.sqrt(np.sum(media_norm_feats ** 2, -1, keepdims=True))
        template_feats[count_template] = np.sum(media_norm_feats, 0)
    template_norm_feats = sklearn.preprocessing.normalize(template_feats)
    return template_norm_feats, unique_templates, unique_subjectids


def evaluation_1N(query_feats, gallery_feats, query_ids, reg_ids, fars=[0.01, 0.1]):
    similarity = np.dot(query_feats, gallery_feats.T)  # (19593, 3531)

    top_1_count, top_5_count, top_10_count = 0, 0, 0
    pos_sims, neg_sims, non_gallery_sims = [], [], []
    for index, query_id in enumerate(query_ids):
        if query_id in reg_ids:
            gallery_label = np.argwhere(reg_ids == query_id)[0, 0]
            index_sorted = np.argsort(similarity[index])[::-1]

            top_1_count += gallery_label in index_sorted[:1]
            top_5_count += gallery_label in index_sorted[:5]
            top_10_count += gallery_label in index_sorted[:10]

            pos_sims.append(similarity[index][reg_ids == query_id][0])
            neg_sims.append(similarity[index][reg_ids != query_id])
        else:
            non_gallery_sims.append(similarity[index])
    total_pos = len(pos_sims)
    pos_sims, neg_sims, non_gallery_sims = np.array(pos_sims), np.array(neg_sims), np.array(non_gallery_sims)

    correct_pos_cond = pos_sims > neg_sims.max(1)
    non_gallery_sims_sorted = np.sort(non_gallery_sims.max(1))[::-1]
    threshes, recalls = [], []
    for far in fars:
        # thresh = non_gallery_sims_sorted[int(np.ceil(non_gallery_sims_sorted.shape[0] * far)) - 1]
        thresh = non_gallery_sims_sorted[max(int((non_gallery_sims_sorted.shape[0]) * far) - 1, 0)]
        recall = np.logical_and(correct_pos_cond, pos_sims > thresh).sum() / pos_sims.shape[0]
        threshes.append(thresh)
        recalls.append(recall)
        # print("FAR = {:.10f} TPIR = {:.10f} th = {:.10f}".format(far, recall, thresh))
    cmc_scores = list(zip(neg_sims, pos_sims.reshape(-1, 1))) + list(zip(non_gallery_sims, [None] * non_gallery_sims.shape[0]))
    n_counts = {"n_mated": int(total_pos), "n_non_mated": int(non_gallery_sims.shape[0])}            # [S6]
    return top_1_count, top_5_count, top_10_count, threshes, recalls, cmc_scores, n_counts


def evaluate_1N(img_input_feats, templates, medias, meta_dir, fpirs: Sequence[float] = DEFAULT_FPIRS_1N,
                subset="IJBC") -> Dict[str, object]:
    """Thân ``run_model_test_1N`` của [R2] (G1 và G2 đánh giá riêng, lấy trung bình), nhận đặc trưng sẵn. [S6]"""
    g1_templates, g1_ids, g2_templates, g2_ids, probe_mixed_templates, probe_mixed_ids = extract_gallery_prob_data(
        meta_dir, subset)
    g1_templates_feature, g1_unique_templates, g1_unique_ids = image2template_feature_1N(
        img_input_feats, templates, medias, g1_templates, g1_ids
    )
    g2_templates_feature, g2_unique_templates, g2_unique_ids = image2template_feature_1N(
        img_input_feats, templates, medias, g2_templates, g2_ids
    )
    probe_mixed_templates_feature, probe_mixed_unique_templates, probe_mixed_unique_subject_ids = image2template_feature_1N(
        img_input_feats, templates, medias, probe_mixed_templates, probe_mixed_ids
    )
    fars = list(fpirs)
    g1 = evaluation_1N(probe_mixed_templates_feature, g1_templates_feature, probe_mixed_unique_subject_ids, g1_unique_ids, fars)
    g2 = evaluation_1N(probe_mixed_templates_feature, g2_templates_feature, probe_mixed_unique_subject_ids, g2_unique_ids, fars)
    query_num = probe_mixed_templates_feature.shape[0]
    out = {
        "top1_mean": (g1[0] + g2[0]) / query_num, "top5_mean": (g1[1] + g2[1]) / query_num,
        "top10_mean": (g1[2] + g2[2]) / query_num,
        "n_probe_templates": int(query_num), "G1": g1[6], "G2": g2[6],
    }
    mean_tpirs = (np.array(g1[4]) + np.array(g2[4])) / 2
    for i, f in enumerate(fars):
        out[f"tpir@fpir={f:g}"] = float(mean_tpirs[i])
        out[f"G1_tpir@fpir={f:g}"], out[f"G2_tpir@fpir={f:g}"] = float(g1[4][i]), float(g2[4][i])
        out[f"G1_thr@fpir={f:g}"], out[f"G2_thr@fpir={f:g}"] = float(g1[3][i]), float(g2[3][i])
    # dữ liệu phụ để tính FNIR/FPIR tại ngưỡng cố định (không thuộc code gốc)
    out["_feats"] = {"G1": (g1_templates_feature, g1_unique_ids), "G2": (g2_templates_feature, g2_unique_ids),
                     "probe": (probe_mixed_templates_feature, probe_mixed_unique_subject_ids)}
    return out


# =====================================================================================================
# Bổ sung: tỉ lệ tại ngưỡng cố định t (vd. t = b/s học được của UniFace) — dùng hàm đã unit test
# =====================================================================================================
def rates_at_learned_threshold(threshold: float, score_11=None, label_11=None, feats_1N=None) -> Dict[str, float]:
    out: Dict[str, float] = {"threshold": float(threshold)}
    if score_11 is not None:
        r = rates_at_threshold(threshold, scores=np.asarray(score_11), issame=np.asarray(label_11).astype(bool))
        out["tar_11"], out["far_11"] = r["tar"], r["far"]
    if feats_1N is not None:
        pf, pid = feats_1N["probe"]
        for g in ("G1", "G2"):
            gf, gid = feats_1N[g]
            known = np.isin(pid, gid)
            r = rates_at_threshold(threshold, gallery=gf, gallery_ids=gid, probe_known=pf[known],
                                   probe_known_ids=pid[known], probe_unknown=pf[~known])
            out[f"{g}_fnir"], out[f"{g}_fpir"] = r["fnir"], r["fpir"]
        out["fnir_mean"] = (out["G1_fnir"] + out["G2_fnir"]) / 2
        out["fpir_mean"] = (out["G1_fpir"] + out["G2_fpir"]) / 2
    return out


# =====================================================================================================
# Chạy trọn: Step 1–5 của [R1] (1:1) + 1:N của [R2], một lần trích đặc trưng
# =====================================================================================================
def evaluate_ijbc(backbone, image_path: str, device, batch_size: int = 128, emb_dim: int = 512,
                  target: str = "IJBC", fprs_11: Sequence[float] = DEFAULT_FPRS_11,
                  fpirs_1N: Sequence[float] = DEFAULT_FPIRS_1N, do_1N: bool = True,
                  threshold: Optional[float] = None, save_dir: Optional[str] = None,
                  max_images: Optional[int] = None) -> Dict[str, object]:
    """``image_path`` = thư mục chứa ``loose_crop/`` và ``meta/`` (vd. /kaggle/input/face-ibj-c/IJBC).
    ``max_images`` chỉ dùng để chạy thử nhanh (kết quả khi đó KHÔNG có nghĩa)."""
    use_norm_score = True  # if Ture, TestMode(N1)
    use_detector_score = True  # if Ture, TestMode(D1)
    use_flip_test = True  # if Ture, TestMode(F1)
    res: Dict[str, object] = {"target": target, "flags": "N1D1F2 (flip cộng, giữ norm, nhân điểm detector)"}
    t0 = timeit.default_timer()
    templates, medias = read_template_media_list(os.path.join('%s/meta' % image_path, '%s_face_tid_mid.txt' % target.lower()))
    p1, p2, label = read_template_pair_list(os.path.join('%s/meta' % image_path, '%s_template_pair_label.txt' % target.lower()))
    img_path = '%s/loose_crop' % image_path
    img_list_path = '%s/meta/%s_name_5pts_score.txt' % (image_path, target.lower())
    with open(img_list_path) as img_list:
        files = img_list.readlines()
    if max_images:
        files, templates, medias = files[:max_images], templates[:max_images], medias[:max_images]
        keep = np.isin(p1, templates) & np.isin(p2, templates)
        p1, p2, label = p1[keep], p2[keep], label[keep]
    img_feats, faceness_scores = get_image_feature(img_path, files, backbone, device, batch_size, emb_dim)
    res["n_images"] = int(img_feats.shape[0])
    res["seconds_features"] = timeit.default_timer() - t0

    if use_flip_test:
        # add --- F2
        img_input_feats = img_feats[:, 0:img_feats.shape[1] // 2] + img_feats[:, img_feats.shape[1] // 2:]
    else:
        img_input_feats = img_feats[:, 0:img_feats.shape[1] // 2]
    if use_norm_score:
        img_input_feats = img_input_feats
    else:
        # normalise features to remove norm information
        img_input_feats = img_input_feats / np.sqrt(np.sum(img_input_feats ** 2, -1, keepdims=True))
    if use_detector_score:
        img_input_feats = img_input_feats * faceness_scores[:, np.newaxis]
    else:
        img_input_feats = img_input_feats

    template_norm_feats, unique_templates = image2template_feature(img_input_feats, templates, medias)
    score = verification(template_norm_feats, unique_templates, p1, p2)
    res["1:1"] = safe_tpr_at_fpr(label, score, fprs_11)
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        np.save(os.path.join(save_dir, "%s_11_scores.npy" % target.lower()), score)
    feats_1N = None
    if do_1N and not max_images:
        r1n = evaluate_1N(img_input_feats, templates, medias, '%s/meta' % image_path, fpirs_1N, target)
        feats_1N = r1n.pop("_feats")
        res["1:N"] = r1n
    if threshold is not None:
        res["at_threshold"] = rates_at_learned_threshold(threshold, score, label, feats_1N)
    res["seconds_total"] = timeit.default_timer() - t0
    return res
